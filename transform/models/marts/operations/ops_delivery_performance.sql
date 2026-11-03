-- Delivery SLA performance by month, region and city tier,
-- and how lateness feeds through to customer ratings.

with orders as (

    select * from {{ ref('fct_orders') }}
    where delivered_at is not null

),

customers as (

    select customer_id, region, city_tier from {{ ref('dim_customers') }}

)

select
    orders.order_month,
    customers.region,
    customers.city_tier,
    count(*)                                                            as delivered_orders,
    avg(orders.delivery_days)                                           as avg_delivery_days,
    quantile_cont(orders.delivery_days, 0.9)                            as p90_delivery_days,
    avg(orders.hours_to_ship)                                           as avg_hours_to_ship,
    {{ safe_divide('count(*) filter (where not orders.is_delivered_late)', 'count(*)') }}
                                                                        as on_time_rate,
    avg(orders.delivery_delay_days) filter (where orders.is_delivered_late)
                                                                        as avg_days_late_when_late,
    count(orders.review_rating)                                         as reviews,
    avg(orders.review_rating)                                           as avg_rating,
    avg(orders.review_rating) filter (where not orders.is_delivered_late)
                                                                        as avg_rating_on_time,
    avg(orders.review_rating) filter (where orders.is_delivered_late)  as avg_rating_late

from orders
inner join customers
    on orders.customer_id = customers.customer_id
group by 1, 2, 3
