-- Orphan check: an order with no line items or no payment is a pipeline bug.
select order_id, line_count, payment_total
from {{ ref('fct_orders') }}
where line_count is null
   or payment_total is null
