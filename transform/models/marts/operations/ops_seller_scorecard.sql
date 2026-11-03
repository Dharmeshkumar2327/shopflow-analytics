-- Seller scorecard: volume, reliability and customer experience rolled into
-- a composite score and tier. Sellers with < 30 orders are not tiered.

with items as (

    select
        seller_id,
        order_id,
        order_status,
        gross_amount,
        recognized_revenue,
        recognized_gross_margin
    from {{ ref('fct_order_items') }}

),

orders as (

    select order_id, is_delivered_late, hours_to_ship, review_rating
    from {{ ref('fct_orders') }}

),

seller_orders as (

    -- one row per seller x order (an order can contain several sellers)
    select
        items.seller_id,
        items.order_id,
        any_value(items.order_status)       as order_status,
        sum(items.gross_amount)             as gmv,
        sum(items.recognized_revenue)       as revenue,
        sum(items.recognized_gross_margin)  as gross_margin
    from items
    group by 1, 2

),

metrics as (

    select
        seller_orders.seller_id,
        count(*)                                                                as orders,
        sum(seller_orders.gmv) filter (where seller_orders.order_status <> 'cancelled')
                                                                                as gmv,
        sum(seller_orders.revenue)                                              as net_revenue,
        sum(seller_orders.gross_margin)                                         as gross_margin,
        {{ safe_divide("count(*) filter (where seller_orders.order_status = 'cancelled')", 'count(*)') }}
                                                                                as cancellation_rate,
        {{ safe_divide("count(*) filter (where seller_orders.order_status = 'returned')",
                       "count(*) filter (where seller_orders.order_status in ('delivered', 'returned'))") }}
                                                                                as return_rate,
        {{ safe_divide('count(*) filter (where orders.is_delivered_late = false)',
                       'count(orders.is_delivered_late)') }}                    as on_time_rate,
        avg(orders.hours_to_ship)                                               as avg_hours_to_ship,
        avg(orders.review_rating)                                               as avg_rating
    from seller_orders
    inner join orders
        on seller_orders.order_id = orders.order_id
    group by 1

),

scored as (

    select
        metrics.*,
        round(100 * (
              0.35 * coalesce(on_time_rate, 0)
            + 0.25 * (1 - coalesce(cancellation_rate, 0))
            + 0.15 * (1 - coalesce(return_rate, 0))
            + 0.25 * coalesce(avg_rating, 0) / 5
        ), 1)                                                                   as seller_score
    from metrics

)

select
    sellers.seller_id,
    sellers.seller_name,
    sellers.region,
    sellers.city_tier,
    sellers.tenure_months,
    scored.* exclude (seller_id),
    case
        when scored.orders < 30      then 'Not rated (< 30 orders)'
        when scored.seller_score >= 86 then 'Gold'
        when scored.seller_score >= 83 then 'Silver'
        when scored.seller_score >= 80 then 'Bronze'
        else 'Needs Improvement'
    end                                                                         as seller_tier,
    rank() over (order by scored.net_revenue desc)                              as revenue_rank

from scored
inner join {{ ref('dim_sellers') }} as sellers
    on scored.seller_id = sellers.seller_id
