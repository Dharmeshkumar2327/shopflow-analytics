-- Finance control: what customers paid must equal what they were charged
-- (tolerance of 1 rupee for rounding across split tenders).
select
    order_id,
    order_total,
    payment_total,
    payment_total - order_total as difference
from {{ ref('fct_orders') }}
where abs(coalesce(payment_total, 0) - order_total) > 1
