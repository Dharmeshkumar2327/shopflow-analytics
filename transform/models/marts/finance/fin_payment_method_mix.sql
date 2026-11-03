-- How customers pay, by month: tracks UPI adoption and the shift away from cash on delivery.

with orders as (

    select order_month, primary_payment_method, order_total, is_cancelled
    from {{ ref('fct_orders') }}

),

by_method as (

    select
        order_month,
        primary_payment_method                                  as payment_method,
        count(*)                                                as orders,
        sum(order_total)                                        as order_value,
        count(*) filter (where is_cancelled)                    as cancelled_orders
    from orders
    group by 1, 2

)

select
    order_month,
    payment_method,
    orders,
    order_value,
    {{ safe_divide('orders', 'sum(orders) over (partition by order_month)') }}
                                                                as order_share,
    {{ safe_divide('order_value', 'sum(order_value) over (partition by order_month)') }}
                                                                as value_share,
    {{ safe_divide('order_value', 'orders') }}                  as avg_order_value,
    {{ safe_divide('cancelled_orders', 'orders') }}             as cancellation_rate

from by_method
