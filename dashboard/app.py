"""
ShopFlow Executive Dashboard
Reads only from the dbt marts in data/shopflow.duckdb.

    streamlit run dashboard/app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import queries as q

DB_PATH = Path(os.environ.get("DUCKDB_PATH", Path(__file__).resolve().parents[1] / "data" / "shopflow.duckdb"))

# Categorical slots in fixed order (CVD-validated); sequential blue ramp for magnitude.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
MUTED = "#8a8984"
TIER_COLORS = {"Tier 1": SERIES[0], "Tier 2": SERIES[1], "Tier 3": SERIES[2]}

st.set_page_config(page_title="ShopFlow Analytics", layout="wide")


# ----------------------------------------------------------------------------- data
@st.cache_data(show_spinner=False)
def load(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql).df()


def inr(value: float) -> str:
    """Indian-style money: Rs 4.93 Cr / Rs 12.4 L / Rs 3,489."""
    if value is None or pd.isna(value):
        return "-"
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:,.2f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:,.1f} L"
    return f"₹{value:,.0f}"


def pct_delta(cur: float, prev: float) -> str | None:
    if prev in (0, None) or pd.isna(prev):
        return None
    return f"{(cur - prev) / prev:+.1%}"


def style(fig: go.Figure, height: int = 360, y_title: str | None = None, pct: bool = False) -> go.Figure:
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
        hovermode="x unified", font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(gridcolor="#ecebe7", title=y_title, tickformat=".0%" if pct else None, zeroline=False)
    fig.update_traces(selector=dict(type="scatter"), line=dict(width=2))
    return fig


if not DB_PATH.exists():
    st.error(f"Warehouse not found at `{DB_PATH}`. Run `python pipeline.py` first.")
    st.stop()

kpis = load(q.MONTHLY_KPIS)
kpis["order_month"] = pd.to_datetime(kpis["order_month"])

# ----------------------------------------------------------------------------- header & filter
st.title("ShopFlow — Marketplace Performance")
st.caption("Indian e-commerce marketplace · dbt + DuckDB modern data stack · all figures in INR · "
           "revenue = delivered orders only")

fiscal_years = sorted(kpis["fiscal_year"].unique())
default_fy = fiscal_years[-1]
fy = st.selectbox("Fiscal year (Apr–Mar)", fiscal_years, index=fiscal_years.index(default_fy))

cur = kpis[kpis["fiscal_year"] == fy]
# like-for-like comparison: the same calendar months one year earlier
prev = kpis[kpis["order_month"].isin(cur["order_month"] - pd.DateOffset(years=1))]
months_label = f"{cur['order_month'].min():%b %Y} – {cur['order_month'].max():%b %Y}"

tab_exec, tab_cust, tab_mkt, tab_ops = st.tabs(
    ["Executive overview", "Customers & retention", "Marketing efficiency", "Operations"]
)

# ============================================================================ EXECUTIVE
with tab_exec:
    st.caption(f"{fy} · {months_label} · deltas vs the same months a year earlier")
    c1, c2, c3, c4, c5 = st.columns(5)
    rev, rev_p = cur["net_revenue"].sum(), prev["net_revenue"].sum()
    c1.metric("Net revenue", inr(rev), pct_delta(rev, rev_p))
    c2.metric("Orders placed", f"{cur['orders_placed'].sum():,}",
              pct_delta(cur["orders_placed"].sum(), prev["orders_placed"].sum()))
    aov = rev / cur["orders_completed"].sum()
    aov_p = rev_p / prev["orders_completed"].sum() if len(prev) else None
    c3.metric("Avg order value", inr(aov), pct_delta(aov, aov_p))
    gm = cur["gross_margin"].sum() / rev
    gm_p = prev["gross_margin"].sum() / rev_p if rev_p else None
    c4.metric("Gross margin", f"{gm:.1%}", f"{(gm - gm_p) * 100:+.1f} pts" if gm_p else None)
    c5.metric("New customers", f"{cur['new_customers'].sum():,}",
              pct_delta(cur["new_customers"].sum(), prev["new_customers"].sum()))

    left, right = st.columns([3, 2])
    with left:
        fig = go.Figure()
        fig.add_bar(x=kpis["order_month"], y=kpis["net_revenue"], name="Net revenue",
                    marker_color=[SERIES[0] if f == fy else BLUE_RAMP[1] for f in kpis["fiscal_year"]],
                    hovertemplate="%{x|%b %Y}: ₹%{y:,.0f}<extra></extra>")
        fig.add_scatter(x=kpis["order_month"], y=kpis["net_revenue_3m_avg"], name="3-month average",
                        line=dict(color=SERIES[1]), hovertemplate="3m avg: ₹%{y:,.0f}<extra></extra>")
        fig.update_layout(title="Monthly net revenue — festive-season peaks every Oct/Nov")
        st.plotly_chart(style(fig, y_title="INR"))
    with right:
        cat = load(q.CATEGORY)
        cat = cat[cat["fiscal_year"] == fy].sort_values("net_revenue")
        fig = px.bar(cat, x="net_revenue", y="category", orientation="h",
                     hover_data={"gross_margin_pct": ":.1%", "return_rate": ":.1%", "net_revenue": ":,.0f"},
                     color_discrete_sequence=[SERIES[0]], title="Revenue by category")
        fig.update_traces(marker_cornerradius=4)
        st.plotly_chart(style(fig, y_title=None).update_layout(hovermode="closest"))

    left, right = st.columns(2)
    with left:
        mix = load(q.PAYMENT_MIX)
        mix["payment_method"] = mix["payment_method"].map(
            {"upi": "UPI", "cod": "Cash on delivery", "credit_card": "Credit card", "debit_card": "Debit card"})
        fig = px.line(mix, x="order_month", y="order_share", color="payment_method",
                      color_discrete_sequence=SERIES, title="Payment mix — UPI up, cash on delivery down")
        st.plotly_chart(style(fig, pct=True))
    with right:
        rates = kpis.melt(id_vars="order_month", value_vars=["cancellation_rate", "return_rate"],
                          var_name="metric", value_name="rate")
        rates["metric"] = rates["metric"].map({"cancellation_rate": "Cancellation rate",
                                               "return_rate": "Return rate"})
        fig = px.line(rates, x="order_month", y="rate", color="metric",
                      color_discrete_sequence=SERIES, title="Cancellations & returns")
        st.plotly_chart(style(fig, pct=True))

# ============================================================================ CUSTOMERS
with tab_cust:
    cohorts = load(q.COHORTS)
    cohorts["cohort"] = pd.to_datetime(cohorts["cohort_month"]).dt.strftime("%Y-%m")
    heat = cohorts.pivot(index="cohort", columns="months_since_first_order", values="retention_rate")
    fig = px.imshow(heat.iloc[:, 1:], color_continuous_scale=BLUE_RAMP, aspect="auto",
                    labels=dict(x="Months since first order", y="First-order cohort", color="Retained"),
                    title="Cohort retention — share of each cohort ordering again in month N")
    fig.update_coloraxes(colorbar_tickformat=".0%")
    fig.update_traces(hovertemplate="Cohort %{y}, month %{x}: %{z:.1%}<extra></extra>")
    st.plotly_chart(style(fig, height=520).update_layout(hovermode="closest"))

    left, right = st.columns(2)
    with left:
        # weight each cohort's curve by its size
        cohorts["cum_revenue"] = cohorts["cumulative_revenue_per_customer"] * cohorts["cohort_size"]
        curve = cohorts.groupby("months_since_first_order", as_index=False)[["cum_revenue", "cohort_size"]].sum()
        curve["ltv"] = curve["cum_revenue"] / curve["cohort_size"]
        fig = px.line(curve, x="months_since_first_order", y="ltv", markers=True,
                      color_discrete_sequence=[SERIES[0]], title="Customer lifetime value curve")
        fig.update_traces(marker_size=8, hovertemplate="Month %{x}: ₹%{y:,.0f} per customer<extra></extra>")
        st.plotly_chart(style(fig, y_title="Cumulative revenue per customer (INR)")
                        .update_xaxes(title="Months since first order"))
    with right:
        life = load(q.LIFECYCLE)
        order = ["active", "at_risk", "churned", "never_purchased"]
        life["lifecycle_status"] = pd.Categorical(life["lifecycle_status"], order, ordered=True)
        life = life.sort_values("lifecycle_status")
        fig = px.bar(life, x="lifecycle_status", y="customers", text="customers",
                     color_discrete_sequence=[SERIES[0]], title="Customer base by lifecycle status")
        fig.update_traces(marker_cornerradius=4, textposition="outside")
        st.plotly_chart(style(fig).update_layout(hovermode="closest"))

    st.subheader("RFM segments & recommended CRM actions")
    rfm = load(q.RFM)
    st.dataframe(
        rfm, hide_index=True,
        column_config={
            "rfm_segment": "Segment", "recommended_action": "Recommended action",
            "customers": st.column_config.NumberColumn("Customers", format="%d"),
            "lifetime_revenue": st.column_config.NumberColumn("Lifetime revenue (₹)", format="%.0f"),
            "avg_recency_days": st.column_config.NumberColumn("Avg days since order", format="%.0f"),
            "avg_orders": st.column_config.NumberColumn("Avg orders", format="%.1f"),
        },
    )

# ============================================================================ MARKETING
with tab_mkt:
    ch = load(q.CHANNELS)
    st.caption("CAC = paid media spend ÷ new customers. LTV = gross margin from a customer's first 180 days. "
               "Only cohorts that have completed the 180-day window are included.")
    paid = ch[ch["spend"] > 0]
    cols = st.columns(len(paid))
    for col, (_, r) in zip(cols, paid.iterrows()):
        col.metric(f"{r['channel'].replace('_', ' ').title()} — LTV:CAC", f"{r['ltv_to_cac']:.1f}x",
                   help=f"CAC {inr(r['cac'])} · 180-day margin {inr(r['ltv_180d_margin'])}")

    left, right = st.columns(2)
    with left:
        long = paid.melt(id_vars="channel", value_vars=["cac", "ltv_180d_margin"],
                         var_name="measure", value_name="inr")
        long["measure"] = long["measure"].map({"cac": "CAC", "ltv_180d_margin": "180-day margin per customer"})
        fig = px.bar(long, x="channel", y="inr", color="measure", barmode="group",
                     color_discrete_sequence=SERIES, title="What a customer costs vs what they earn us")
        fig.update_traces(marker_cornerradius=4)
        st.plotly_chart(style(fig, y_title="INR").update_layout(hovermode="closest"))
    with right:
        trend = load(q.CHANNEL_TREND)
        fig = px.line(trend, x="quarter", y="ltv_to_cac", color="channel", markers=True,
                      color_discrete_sequence=SERIES, title="LTV:CAC by quarter — is social getting expensive?")
        fig.add_hline(y=3, line_dash="dot", line_color=MUTED, annotation_text="3x rule of thumb")
        fig.update_traces(marker_size=8)
        st.plotly_chart(style(fig, y_title="LTV : CAC"))

    st.dataframe(ch, hide_index=True, column_config={
        "spend": st.column_config.NumberColumn("Spend (₹)", format="%.0f"),
        "cac": st.column_config.NumberColumn("CAC (₹)", format="%.0f"),
        "ltv_180d_margin": st.column_config.NumberColumn("180d margin / customer (₹)", format="%.0f"),
        "ltv_to_cac": st.column_config.NumberColumn("LTV:CAC", format="%.2f"),
    })

# ============================================================================ OPERATIONS
with tab_ops:
    left, right = st.columns(2)
    with left:
        dt = load(q.DELIVERY_TREND)
        fig = px.line(dt, x="order_month", y="on_time_rate", color="city_tier",
                      color_discrete_map=TIER_COLORS, title="On-time delivery rate by city tier")
        st.plotly_chart(style(fig, pct=True))
    with right:
        dr = load(q.DELIVERY_RATING)
        long = dr.melt(id_vars="city_tier", value_vars=["rating_when_on_time", "rating_when_late"],
                       var_name="delivery", value_name="rating")
        long["delivery"] = long["delivery"].map({"rating_when_on_time": "Delivered on time",
                                                 "rating_when_late": "Delivered late"})
        fig = px.bar(long, x="city_tier", y="rating", color="delivery", barmode="group",
                     color_discrete_sequence=SERIES, text_auto=".2f",
                     title="A late delivery costs ~1 star")
        fig.update_traces(marker_cornerradius=4)
        st.plotly_chart(style(fig, y_title="Average rating (1–5)").update_layout(hovermode="closest")
                        .update_yaxes(range=[0, 5]))

    st.subheader("Seller scorecard")
    sellers = load(q.SELLERS)
    tiers = st.multiselect("Seller tier", sorted(sellers["seller_tier"].unique()),
                           default=sorted(sellers["seller_tier"].unique()))
    st.dataframe(
        sellers[sellers["seller_tier"].isin(tiers)], hide_index=True,
        column_config={
            "net_revenue": st.column_config.NumberColumn("Net revenue (₹)", format="%.0f"),
            "on_time_rate": st.column_config.NumberColumn("On-time", format="%.2f"),
            "cancellation_rate": st.column_config.NumberColumn("Cancel rate", format="%.3f"),
            "return_rate": st.column_config.NumberColumn("Return rate", format="%.3f"),
            "avg_rating": st.column_config.NumberColumn("Rating", format="%.2f"),
            "seller_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
        },
    )

st.caption(f"Source: dbt marts in `{DB_PATH.name}` · lineage & definitions: `dbt docs serve`")
