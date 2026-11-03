-- Line-item fact and order fact must agree on recognised item revenue per order.
with items as (
    select order_id, sum(recognized_revenue) as item_revenue
    from {{ ref('fct_order_items') }}
    group by order_id
)
select
    orders.order_id,
    orders.recognized_revenue - orders.shipping_fee * cast(orders.is_completed as integer) as order_item_revenue,
    items.item_revenue
from {{ ref('fct_orders') }} as orders
inner join items
    on orders.order_id = items.order_id
where abs(
    (orders.recognized_revenue - orders.shipping_fee * cast(orders.is_completed as integer))
    - items.item_revenue
) > 0.01
