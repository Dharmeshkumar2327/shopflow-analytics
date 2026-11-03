"""
Synthetic data generator for ShopFlow — a fictional Indian e-commerce marketplace.

Produces raw CSV extracts the way an operational system would hand them over:
messy casing, duplicate customer records, string-typed timestamps, mixed payment
labels. Cleaning all of that up is the job of the dbt staging layer.

Business patterns baked in (so the analytics have something real to find):
  * Growth trend in signups across FY2022-23 .. FY2025-26
  * Festive-season spikes (Diwali, Republic Day & Independence Day sales)
  * Customer churn that decays cohorts over time
  * UPI adoption rising, Cash-on-Delivery falling
  * Slower, later deliveries in Tier-3 cities -> lower review ratings
  * Higher return rates in Fashion

Usage:
    python scripts/generate_data.py                 # default 10k customers
    python scripts/generate_data.py --customers 20000 --seed 7
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

START = date(2023, 1, 1)
END = date(2025, 12, 31)
LOADED_AT = datetime(2026, 1, 1, 2, 0, 0)  # nightly batch that extracted this data

CITIES = [
    # city, state, tier, weight
    ("Bengaluru", "Karnataka", 1, 10), ("Mumbai", "Maharashtra", 1, 10),
    ("Delhi", "Delhi", 1, 10), ("Hyderabad", "Telangana", 1, 8),
    ("Chennai", "Tamil Nadu", 1, 7), ("Kolkata", "West Bengal", 1, 6),
    ("Pune", "Maharashtra", 1, 6), ("Ahmedabad", "Gujarat", 1, 5),
    ("Jaipur", "Rajasthan", 2, 4), ("Lucknow", "Uttar Pradesh", 2, 4),
    ("Kochi", "Kerala", 2, 3), ("Indore", "Madhya Pradesh", 2, 3),
    ("Chandigarh", "Chandigarh", 2, 3), ("Bhubaneswar", "Odisha", 2, 2),
    ("Patna", "Bihar", 2, 3), ("Guwahati", "Assam", 2, 2),
    ("Coimbatore", "Tamil Nadu", 2, 3), ("Nagpur", "Maharashtra", 2, 2),
    ("Visakhapatnam", "Andhra Pradesh", 2, 2), ("Surat", "Gujarat", 2, 3),
    ("Mysuru", "Karnataka", 3, 2), ("Ranchi", "Jharkhand", 3, 2),
    ("Dehradun", "Uttarakhand", 3, 1), ("Raipur", "Chhattisgarh", 3, 1),
    ("Varanasi", "Uttar Pradesh", 3, 2), ("Madurai", "Tamil Nadu", 3, 1),
    ("Thiruvananthapuram", "Kerala", 3, 1), ("Gaya", "Bihar", 3, 1),
    ("Shillong", "Meghalaya", 3, 1), ("Jammu", "Jammu and Kashmir", 3, 1),
]

CATEGORIES = {
    # category: (sub_categories, price_low, price_high, cost_ratio, return_rate, popularity)
    "Electronics": (["Mobiles", "Laptops", "Audio", "Accessories", "Smart Home"], 299, 59999, 0.84, 0.04, 1.0),
    "Fashion": (["Men Clothing", "Women Clothing", "Footwear", "Watches", "Bags"], 299, 4999, 0.48, 0.14, 1.6),
    "Home & Kitchen": (["Cookware", "Appliances", "Decor", "Furnishing", "Storage"], 199, 14999, 0.62, 0.04, 1.1),
    "Beauty": (["Skincare", "Haircare", "Makeup", "Fragrance"], 99, 2999, 0.52, 0.03, 1.0),
    "Books": (["Fiction", "Exam Prep", "Self Help", "Children"], 149, 1499, 0.72, 0.01, 0.7),
    "Sports": (["Fitness", "Cricket", "Cycling", "Yoga"], 299, 9999, 0.60, 0.05, 0.6),
    "Grocery": (["Staples", "Snacks", "Beverages", "Personal Care"], 49, 999, 0.82, 0.01, 1.2),
    "Toys": (["Board Games", "Educational", "Soft Toys", "Remote Control"], 199, 4999, 0.56, 0.03, 0.5),
}

BRAND_PREFIX = ["Nova", "Desi", "Urban", "Lotus", "Indus", "Zen", "Tara", "Veda", "Kaveri", "Swift",
                "Aero", "Bodhi", "Ganga", "Pixel", "Sona", "Mitra", "Arka", "Neel", "Ruhi", "Vayu"]
BRAND_SUFFIX = ["Labs", "Wear", "Home", "Co", "Tech", "Essentials", "Craft", "Living", "Works", "Basics"]

CHANNELS = ["organic", "paid_search", "social", "referral", "email", "affiliate"]
CHANNEL_WEIGHTS = [0.30, 0.22, 0.20, 0.10, 0.08, 0.10]
CHANNEL_CAC = {"paid_search": 520, "social": 410, "affiliate": 330, "email": 240}  # INR per new customer
CHANNEL_LOYALTY = {"organic": 1.15, "paid_search": 0.95, "social": 0.80, "referral": 1.30,
                   "email": 1.20, "affiliate": 0.75}  # multiplies purchase rate & lifetime

# Evening-heavy shopping pattern (share of orders by hour of day)
HOUR_W = np.array([1, .5, .3, .2, .2, .3, .6, 1, 1.5, 2, 2.3, 2.5, 2.7, 2.6, 2.4,
                   2.3, 2.4, 2.8, 3.3, 3.8, 4.2, 4.0, 3.0, 2.0])
HOUR_W = HOUR_W / HOUR_W.sum()

# Festival anchor dates (sale windows are built around them)
DIWALI = [date(2023, 11, 12), date(2024, 11, 1), date(2025, 10, 20)]


def day_weights(days: pd.DatetimeIndex) -> np.ndarray:
    """Relative order intensity for each calendar day (seasonality)."""
    w = np.ones(len(days))
    w[days.dayofweek >= 5] *= 1.15                      # weekends
    w[days.day <= 5] *= 1.10                            # salary week
    for d in DIWALI:
        festive = (days >= pd.Timestamp(d) - pd.Timedelta(days=30)) & (days <= pd.Timestamp(d) + pd.Timedelta(days=7))
        peak = (days >= pd.Timestamp(d) - pd.Timedelta(days=7)) & (days <= pd.Timestamp(d))
        w[festive] *= 1.7
        w[peak] *= 1.6
    for y in (2023, 2024, 2025):
        w[(days >= pd.Timestamp(y, 1, 19)) & (days <= pd.Timestamp(y, 1, 26))] *= 1.45   # Republic Day sale
        w[(days >= pd.Timestamp(y, 8, 8)) & (days <= pd.Timestamp(y, 8, 15))] *= 1.45    # Independence Day sale
    return w


def is_sale_day(ts: pd.Timestamp) -> bool:
    d = ts.date()
    for dw in DIWALI:
        if dw - timedelta(days=30) <= d <= dw + timedelta(days=7):
            return True
    return (d.month == 1 and 19 <= d.day <= 26) or (d.month == 8 and 8 <= d.day <= 15)


def messy_case(rng: np.random.Generator, s: str, p: float = 0.08) -> str:
    """Randomly corrupt casing / whitespace like a hand-keyed source system."""
    r = rng.random()
    if r < p / 3:
        return s.upper()
    if r < 2 * p / 3:
        return s.lower() + " "
    if r < p:
        return "  " + s
    return s


def fmt_ts(ts) -> str:
    return "" if ts is None or pd.isna(ts) else pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def generate(n_customers: int, seed: int, out_dir: Path) -> None:
    rng = np.random.default_rng(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_days = pd.date_range(START, END, freq="D")
    season = day_weights(all_days)
    n_days = len(all_days)

    # ---------------------------------------------------------------- sellers
    city_w = np.array([c[3] for c in CITIES], dtype=float)
    city_w /= city_w.sum()
    n_sellers = max(50, n_customers // 32)
    seller_city_idx = rng.choice(len(CITIES), n_sellers, p=city_w)
    seller_quality = rng.beta(6, 2, n_sellers)  # drives late shipping & cancellations
    sellers = pd.DataFrame({
        "seller_id": [f"S{i:05d}" for i in range(1, n_sellers + 1)],
        "seller_name": [f"{rng.choice(BRAND_PREFIX)} {rng.choice(['Traders', 'Retail', 'Mart', 'Enterprises', 'Store', 'Bazaar'])}"
                        for _ in range(n_sellers)],
        "city": [CITIES[i][0] for i in seller_city_idx],
        "state": [CITIES[i][1] for i in seller_city_idx],
        "onboarded_at": [fmt_ts(pd.Timestamp(START) - pd.Timedelta(days=int(rng.integers(0, 900))))
                         for _ in range(n_sellers)],
    })

    # --------------------------------------------------------------- products
    n_products = max(200, n_customers // 6)
    cat_names = list(CATEGORIES)
    cat_pop = np.array([CATEGORIES[c][5] for c in cat_names])
    prod_cat = rng.choice(cat_names, n_products, p=cat_pop / cat_pop.sum())
    rows = []
    for i, cat in enumerate(prod_cat, start=1):
        subs, lo, hi, cost_ratio, _, _ = CATEGORIES[cat]
        # right-skewed: most products are cheap, a long tail is expensive
        price = float(np.exp(np.log(lo) + rng.random() ** 1.8 * (np.log(hi) - np.log(lo))))
        price = round(price / 10) * 10 - 1  # Indian ".99"-style pricing: 1299, 499 ...
        price = max(price, lo)
        brand = f"{rng.choice(BRAND_PREFIX)}{rng.choice(BRAND_SUFFIX)}"
        sub = rng.choice(subs)
        created = pd.Timestamp(START) + pd.Timedelta(days=int(rng.integers(-365, 700)))
        rows.append({
            "product_id": f"P{i:06d}",
            "product_name": f"{brand} {sub} {rng.choice(['Pro', 'Lite', 'Max', 'Classic', 'Plus', 'Prime', 'Neo'])}",
            "category": cat,
            "sub_category": sub,
            "brand": brand,
            "seller_id": sellers.seller_id.iloc[int(rng.integers(0, n_sellers))],
            "list_price": f"{price:.2f}",
            "cost_price": f"{price * cost_ratio * rng.uniform(0.9, 1.1):.2f}",
            "weight_grams": int(rng.integers(50, 8000)),
            "is_active": "Y" if rng.random() > 0.05 else "N",
            "created_at": fmt_ts(created),
            "updated_at": fmt_ts(created + pd.Timedelta(days=int(rng.integers(0, 300)))),
        })
    products = pd.DataFrame(rows)
    prod_created = pd.to_datetime(products.created_at)
    prod_pop = rng.zipf(1.6, n_products).astype(float)
    prod_pop = np.minimum(prod_pop, 200)
    prod_price = products.list_price.astype(float).to_numpy()
    prod_seller_idx = products.seller_id.str[1:].astype(int).to_numpy() - 1

    # -------------------------------------------------------------- customers
    trend = np.linspace(1.0, 2.6, n_days)  # business is growing
    signup_p = trend * season
    signup_p /= signup_p.sum()
    signup_idx = np.sort(rng.choice(n_days, n_customers, p=signup_p))
    cust_city_idx = rng.choice(len(CITIES), n_customers, p=city_w)
    cust_channel = rng.choice(CHANNELS, n_customers, p=CHANNEL_WEIGHTS)
    domains = ["gmail.com", "yahoo.co.in", "outlook.com", "rediffmail.com", "hotmail.com"]
    customers = pd.DataFrame({
        "customer_id": [f"C{i:07d}" for i in range(1, n_customers + 1)],
        "email": [messy_case(rng, f"user{i:07d}@{rng.choice(domains, p=[.62, .12, .12, .06, .08])}", 0.1)
                  for i in range(1, n_customers + 1)],
        "city": [messy_case(rng, CITIES[i][0]) for i in cust_city_idx],
        "state": [messy_case(rng, CITIES[i][1]) for i in cust_city_idx],
        "signup_date": [all_days[i].strftime("%Y-%m-%d") for i in signup_idx],
        "acquisition_channel": cust_channel,
        "_loaded_at": fmt_ts(LOADED_AT),
    })

    # ----------------------------------------------------------------- orders
    order_rows, item_rows, pay_rows, review_rows = [], [], [], []
    order_seq = item_seq = pay_seq = review_seq = 0
    ts_end = pd.Timestamp(END) + pd.Timedelta(hours=23, minutes=59)

    for c in range(n_customers):
        if rng.random() < 0.13:  # signed up but never purchased
            continue
        loyalty = CHANNEL_LOYALTY[cust_channel[c]]
        tier = CITIES[cust_city_idx[c]][2]
        first_idx = min(n_days - 1, signup_idx[c] + int(rng.exponential(6)))
        lifetime_days = int(rng.exponential(330 * loyalty)) + 1
        last_idx = min(n_days - 1, first_idx + lifetime_days)
        rate = rng.lognormal(np.log(1 / 70 * loyalty), 0.6)  # orders per active day
        n_orders = 1 + rng.poisson(rate * (last_idx - first_idx))
        n_orders = min(n_orders, 60)
        window = np.arange(first_idx, last_idx + 1)
        if len(window) > 1 and n_orders > 1:
            w = season[window[1:]]
            later = rng.choice(window[1:], n_orders - 1, p=w / w.sum())
            order_days = np.concatenate([[first_idx], np.sort(later)])
        else:
            order_days = np.array([first_idx])

        for d_idx in order_days:
            order_seq += 1
            oid = f"O{order_seq:08d}"
            hour = int(rng.choice(24, p=HOUR_W))
            purchased = all_days[d_idx] + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60)),
                                                        seconds=int(rng.integers(0, 60)))
            sale = is_sale_day(purchased)

            # ---- items
            n_items = int(rng.choice([1, 2, 3, 4, 5], p=[.64, .22, .09, .03, .02]))
            available = np.where(prod_created <= purchased)[0]
            pw = prod_pop[available]
            picks = rng.choice(available, min(n_items, len(available)), replace=False, p=pw / pw.sum())
            items_net, has_fashion, primary_seller = 0.0, False, prod_seller_idx[picks[0]]
            order_items = []
            for k, p_idx in enumerate(picks, start=1):
                cat = prod_cat[p_idx]
                qty = int(rng.choice([1, 2, 3, 4], p=[.55, .25, .12, .08])) if cat == "Grocery" else \
                    int(rng.choice([1, 2], p=[.9, .1]))
                unit_price = prod_price[p_idx]
                if sale and rng.random() < 0.65:
                    disc_pct = rng.uniform(0.10, 0.35)
                elif rng.random() < 0.22:
                    disc_pct = rng.uniform(0.03, 0.12)
                else:
                    disc_pct = 0.0
                discount = round(unit_price * qty * disc_pct, 2)
                items_net += unit_price * qty - discount
                has_fashion |= cat == "Fashion"
                item_seq += 1
                order_items.append({
                    "order_id": oid, "order_item_id": k, "product_id": products.product_id.iloc[p_idx],
                    "seller_id": sellers.seller_id.iloc[prod_seller_idx[p_idx]],
                    "quantity": qty, "unit_price": f"{unit_price:.2f}", "discount_amount": f"{discount:.2f}",
                })
            item_rows.extend(order_items)
            shipping_fee = 0.0 if items_net >= 499 else 40.0
            order_total = round(items_net + shipping_fee, 2)

            # ---- status & fulfilment timeline
            sq = seller_quality[primary_seller]
            promised = {1: 6, 2: 7, 3: 9}[tier]
            est_delivery = (purchased + pd.Timedelta(days=promised)).normalize()
            r = rng.random()
            cancel_p = 0.03 + (1 - sq) * 0.08
            return_p = 0.11 if has_fashion else 0.03
            approved = purchased + pd.Timedelta(minutes=int(rng.integers(1, 180)))
            shipped = delivered = pd.NaT
            if r < cancel_p:
                status = "cancelled"
                if rng.random() < 0.4:
                    approved = pd.NaT
            else:
                ship_lag = rng.gamma(2, 0.6) + (1 - sq) * 2.5
                transit = rng.gamma(3, {1: 0.9, 2: 1.4, 3: 2.2}[tier]) + (1.5 if sale else 0)
                shipped = approved + pd.Timedelta(hours=float(ship_lag * 24))
                delivered = shipped + pd.Timedelta(hours=float(transit * 24))
                if shipped > ts_end:
                    status, shipped, delivered = "processing", pd.NaT, pd.NaT
                elif delivered > ts_end:
                    status, delivered = "shipped", pd.NaT
                elif rng.random() < return_p:
                    status = "returned"
                else:
                    status = "delivered"

            coupon = ""
            if sale and rng.random() < 0.35:
                coupon = rng.choice(["DIWALI25", "FESTIVE15", "BIGSALE10", "REPUBLIC20", "FREEDOM15"])
            elif rng.random() < 0.06:
                coupon = rng.choice(["WELCOME100", "NEWUSER50", "SAVE10"])

            order_rows.append({
                "order_id": oid, "customer_id": customers.customer_id.iloc[c],
                "order_status": messy_case(rng, status.capitalize() if rng.random() < .5 else status, 0.12),
                "order_channel": rng.choice(["android", "ios", "web"], p=[.58, .17, .25]),
                "purchased_at": fmt_ts(purchased), "approved_at": fmt_ts(approved),
                "shipped_at": fmt_ts(shipped), "delivered_at": fmt_ts(delivered),
                "estimated_delivery_date": est_delivery.strftime("%Y-%m-%d"),
                "shipping_fee": f"{shipping_fee:.2f}", "coupon_code": coupon,
            })

            # ---- payments (UPI adoption grows over time, COD falls, more COD in Tier 3)
            progress = d_idx / n_days
            methods = ["upi", "credit_card", "debit_card", "cod", "wallet", "netbanking", "emi"]
            mw = np.array([0.44 + 0.16 * progress, 0.13, 0.09, 0.22 - 0.10 * progress + (0.08 if tier == 3 else 0),
                           0.05, 0.04, 0.0])
            if order_total > 10000:
                mw[6] = 0.35
            mw = mw / mw.sum()
            method = rng.choice(methods, p=mw)
            if status == "cancelled":
                pay_status = "voided" if method == "cod" else "refunded"
            elif status == "returned":
                pay_status = "refunded"
            elif method == "cod" and status in ("processing", "shipped"):
                pay_status = "pending"
            else:
                pay_status = "captured"
            paid_at = delivered if method == "cod" and status in ("delivered", "returned") else approved
            label = {"upi": ["UPI", "upi", "Upi"], "credit_card": ["credit_card", "Credit Card", "CREDIT_CARD"],
                     "debit_card": ["debit_card", "Debit Card"], "cod": ["cod", "COD", "Cash on Delivery"],
                     "wallet": ["wallet", "Wallet"], "netbanking": ["netbanking", "Net Banking"],
                     "emi": ["emi", "EMI"]}
            splits = [(method, order_total)]
            if method != "cod" and rng.random() < 0.06 and order_total > 200:
                wallet_part = round(min(order_total - 50, rng.uniform(50, 500)), 2)
                splits = [("wallet", wallet_part), (method if method != "wallet" else "upi",
                                                    round(order_total - wallet_part, 2))]
            for seq, (m, amt) in enumerate(splits, start=1):
                pay_seq += 1
                pay_rows.append({
                    "payment_id": f"PAY{pay_seq:09d}", "order_id": oid, "payment_sequence": seq,
                    "payment_method": rng.choice(label[m]), "payment_status": pay_status,
                    "amount": f"{amt:.2f}",
                    "installments": int(rng.choice([3, 6, 9, 12])) if m == "emi" else 1,
                    "paid_at": fmt_ts(paid_at),
                })

            # ---- reviews: late deliveries & returns hurt ratings
            if status in ("delivered", "returned") and rng.random() < 0.55:
                late_days = max(0.0, (delivered.normalize() - est_delivery).days)
                score = rng.normal(4.45 - 0.45 * min(late_days, 5) - (1.6 if status == "returned" else 0), 0.8)
                review_seq += 1
                review_rows.append({
                    "review_id": f"R{review_seq:08d}", "order_id": oid,
                    "rating": int(np.clip(round(score), 1, 5)),
                    "review_created_at": fmt_ts(delivered + pd.Timedelta(hours=float(rng.uniform(6, 240)))),
                })

    orders = pd.DataFrame(order_rows)
    items = pd.DataFrame(item_rows)
    payments = pd.DataFrame(pay_rows)
    reviews = pd.DataFrame(review_rows)
    reviews = reviews[pd.to_datetime(reviews.review_created_at) <= ts_end]

    # ---------------------------------------------------- marketing spend (daily)
    first_orders = orders.groupby("customer_id").purchased_at.min()
    acq = customers.set_index("customer_id").loc[first_orders.index, ["acquisition_channel"]].copy()
    acq["day"] = pd.to_datetime(first_orders.values).normalize()
    new_by_day = acq.groupby(["day", "acquisition_channel"]).size()
    spend_rows = []
    for ch, cac in CHANNEL_CAC.items():
        # efficiency drifts: social gets more expensive over time, affiliate cheaper
        drift = {"paid_search": (1.0, 1.15), "social": (0.85, 1.45), "affiliate": (1.2, 0.9), "email": (1.0, 1.0)}[ch]
        for i, d in enumerate(all_days):
            new = new_by_day.get((d, ch), 0)
            mult = drift[0] + (drift[1] - drift[0]) * i / n_days
            spend = (new * cac * mult + cac * 0.6) * rng.uniform(0.8, 1.2)
            ctr = {"paid_search": 0.045, "social": 0.012, "affiliate": 0.02, "email": 0.03}[ch]
            cpm = {"paid_search": 180, "social": 95, "affiliate": 120, "email": 15}[ch]
            impressions = int(spend / cpm * 1000)
            spend_rows.append({"spend_date": d.strftime("%Y-%m-%d"), "channel": ch, "spend_inr": f"{spend:.2f}",
                               "impressions": impressions, "clicks": int(impressions * ctr * rng.uniform(.8, 1.2))})
    spend = pd.DataFrame(spend_rows)

    # ---------------------------------------- source-system quirks: duplicates
    # ~1.5% of customers were re-extracted after updating their city (CDC-style duplicates)
    dup = customers.sample(frac=0.015, random_state=seed).copy()
    moved = rng.choice(len(CITIES), len(dup), p=city_w)
    dup["city"] = [CITIES[i][0] for i in moved]
    dup["state"] = [CITIES[i][1] for i in moved]
    dup["_loaded_at"] = fmt_ts(LOADED_AT + timedelta(hours=1))
    customers = pd.concat([customers, dup]).sample(frac=1, random_state=seed).reset_index(drop=True)

    for name, df in {"customers": customers, "sellers": sellers, "products": products, "orders": orders,
                     "order_items": items, "payments": payments, "reviews": reviews,
                     "marketing_spend": spend}.items():
        if "_loaded_at" not in df:
            df["_loaded_at"] = fmt_ts(LOADED_AT)
        df.to_csv(out_dir / f"{name}.csv", index=False)
        print(f"  {name:<16} {len(df):>8,} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--customers", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "raw")
    args = parser.parse_args()
    print(f"Generating ShopFlow data -> {args.out}")
    generate(args.customers, args.seed, args.out)
    print("Done.")


if __name__ == "__main__":
    main()
