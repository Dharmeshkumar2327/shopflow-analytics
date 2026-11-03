-- Adds each customer's purchase sequence so we can separate new vs repeat orders.

with orders as (

    select * from {{ ref('stg_shopflow__orders') }}

)

select
    order_id,
    customer_id,
    purchased_at,
    row_number() over customer_orders                           as customer_order_number,
    row_number() over customer_orders = 1                       as is_first_order,
    lag(purchased_at) over customer_orders                      as previous_order_at,
    date_diff(
        'day',
        cast(lag(purchased_at) over customer_orders as date),
        cast(purchased_at as date)
    )                                                           as days_since_previous_order

from orders
window customer_orders as (
    partition by customer_id
    order by purchased_at, order_id
)
