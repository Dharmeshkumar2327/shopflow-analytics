# Metric definitions

One definition per metric, implemented once in dbt and reused everywhere. If a number
on the dashboard disagrees with a number in a spreadsheet, this page decides which is right.

All money is in INR, GST-inclusive as stored in the source system.

## Revenue

| Metric | Definition | Where |
|---|---|---|
| **GMV** (gross merchandise value) | `list price × quantity` for all orders that were **not cancelled**, before discounts | `fin_monthly_kpis.gmv` |
| **Discounts** | Item-level discounts on non-cancelled orders | `fin_monthly_kpis.discounts` |
| **Order total** | Net item revenue + shipping fee (what the customer is charged) | `fct_orders.order_total` |
| **Net revenue** (recognised) | Order total for orders with status `delivered` only. Cancelled, returned and in-transit orders count as 0 | `fct_orders.recognized_revenue` |
| **Gross margin** | Net item revenue − COGS (cost price × quantity), delivered orders only. Shipping is excluded | `fct_orders.recognized_gross_margin` |
| **AOV** (average order value) | Net revenue ÷ delivered orders | `fin_monthly_kpis.avg_order_value` |

> In-transit orders at the as-of date (`processing`, `shipped`) are not yet recognised, so the
> most recent month always looks lower than it will once those orders are delivered.

## Customers

| Metric | Definition |
|---|---|
| **New customer** | A customer placing their first-ever order (`fct_orders.is_first_order`) |
| **Cohort** | Month of a customer's first order |
| **Retention (month N)** | Share of a cohort that placed *any* order N months after their first-order month |
| **LTV curve** | Cumulative recognised revenue per cohort member, by month since first order |
| **Lifecycle status** | As of `var('as_of_date')`: `active` ≤ 90 days since last order, `at_risk` 91–180, `churned` > 180, `never_purchased` |
| **RFM scores** | Quintiles (1–5, 5 = best) of recency (days since last delivered order), frequency (delivered orders) and monetary value (lifetime net revenue) |

## Marketing

| Metric | Definition |
|---|---|
| **CAC** | Paid-media spend in the month ÷ new customers acquired through that channel in the month |
| **180-day LTV** | Gross margin a new customer generates in the 180 days from their first order |
| **LTV : CAC** | Total 180-day LTV of a channel's new customers ÷ that channel's spend. Only cohorts whose 180-day window has fully elapsed are compared (`is_ltv_window_complete`) |

Organic and referral channels have no media spend, so their CAC and LTV:CAC are null rather than infinite.

## Operations

| Metric | Definition |
|---|---|
| **Delivery days** | Calendar days from order date to delivery date |
| **On-time rate** | Share of delivered orders that arrived on or before the promised (estimated) delivery date |
| **Cancellation rate** | Cancelled orders ÷ orders placed |
| **Return rate** | Returned orders ÷ (delivered + returned orders) |
| **Seller score** | 0–100 = 35% on-time rate + 25% (1 − cancellation rate) + 15% (1 − return rate) + 25% (rating ÷ 5). Tiers: Gold ≥ 86, Silver ≥ 83, Bronze ≥ 80, below that Needs Improvement; sellers with fewer than 30 orders are not rated |

## Calendar

Indian financial year, **1 April – 31 March** (e.g. `FY2024-25`). Fiscal Q1 = Apr–Jun.
Implemented once in `macros/indian_fiscal_calendar.sql` and exposed in `dim_date`.
