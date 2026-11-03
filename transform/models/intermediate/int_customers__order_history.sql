-- Lifetime purchase behaviour per customer (only customers with >= 1 order).

with orders as (

    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.purchased_at,
        o.shipping_fee,
        i.net_item_revenue,
        i.gross_margin
    from {{ ref('stg_shopflow__orders') }} as o
    left join {{ ref('int_orders__items_rolled_up') }} as i
        on o.order_id = i.order_id

)

select
    customer_id,
    min(purchased_at)                                                   as first_order_at,
    max(purchased_at)                                                   as last_order_at,
    max(purchased_at) filter (where order_status = 'delivered')         as last_completed_order_at,
    count(*)                                                            as total_orders,
    count(*) filter (where order_status = 'delivered')                  as completed_orders,
    count(*) filter (where order_status = 'cancelled')                  as cancelled_orders,
    count(*) filter (where order_status = 'returned')                   as returned_orders,
    coalesce(sum(net_item_revenue + shipping_fee)
             filter (where order_status = 'delivered'), 0)              as lifetime_revenue,
    coalesce(sum(gross_margin)
             filter (where order_status = 'delivered'), 0)              as lifetime_gross_margin

from orders
group by customer_id
