{% docs fct_orders %}
**Grain:** one row per order placed on the ShopFlow marketplace.

Combines the order header, rolled-up line items, rolled-up payments, the customer's
purchase sequence, the review and the calendar. This is the single source of truth
for revenue, AOV, conversion of new vs repeat customers and delivery SLAs.

| Measure | Definition |
|---|---|
| `gross_merchandise_value` | list price x quantity, before discounts |
| `net_item_revenue` | after item-level discounts, excluding shipping |
| `order_total` | net_item_revenue + shipping_fee (what the customer pays) |
| `recognized_revenue` | order_total, only when the order is **delivered** |
| `gross_margin` | net_item_revenue - COGS |
{% enddocs %}

{% docs recognized_revenue %}
Revenue is recognised only when an order is **delivered**. Cancelled and returned orders
contribute 0, and orders still `processing` / `shipped` at the as-of date are not yet
recognised. Includes shipping fees; excludes GST (prices are GST-inclusive in the source).
{% enddocs %}

{% docs lifecycle_status %}
Based on days since the customer's last order, as of `var('as_of_date')`:

- `active` - ordered within the last 90 days (`at_risk_after_days`)
- `at_risk` - last order 91-180 days ago
- `churned` - no order for more than 180 days (`churned_after_days`)
- `never_purchased` - signed up but never ordered
{% enddocs %}
