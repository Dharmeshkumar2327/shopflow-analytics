-- One row per order: the central fact table for revenue, fulfilment and customer analytics.
--
-- Revenue definitions (see docs/metrics.md):
--   gross_merchandise_value  list price x qty, before discounts
--   net_item_revenue         after discounts, excluding shipping
--   recognized_revenue       net_item_revenue + shipping, ONLY for delivered orders
--                            (cancelled, returned and in-transit orders are not recognised)

with orders as (

    select * from {{ ref('stg_shopflow__orders') }}

),

items as (

    select * from {{ ref('int_orders__items_rolled_up') }}

),

payments as (

    select * from {{ ref('int_payments__rolled_up') }}

),

sequenced as (

    select * from {{ ref('int_orders__sequenced') }}

),

reviews as (

    select
        order_id,
        arg_max(rating, review_created_at) as review_rating
    from {{ ref('stg_shopflow__reviews') }}
    group by order_id

),

calendar as (

    select date_day, fiscal_year, fiscal_quarter, sale_event_name, is_sale_day
    from {{ ref('dim_date') }}

),

final as (

    select
        -- keys & dates
        orders.order_id,
        orders.customer_id,
        items.primary_seller_id,
        orders.order_date,
        cast(date_trunc('month', orders.order_date) as date)            as order_month,
        calendar.fiscal_year,
        calendar.fiscal_quarter,
        orders.purchased_at,

        -- descriptors
        orders.order_status,
        orders.order_channel,
        items.primary_category,
        payments.primary_payment_method,
        orders.coupon_code,
        calendar.sale_event_name,

        -- customer sequence
        sequenced.customer_order_number,
        sequenced.is_first_order,
        sequenced.days_since_previous_order,

        -- basket
        items.line_count,
        items.units,
        items.distinct_sellers,

        -- money (INR)
        items.gross_merchandise_value,
        items.discount_amount,
        items.net_item_revenue,
        orders.shipping_fee,
        items.net_item_revenue + orders.shipping_fee                    as order_total,
        payments.payment_total,
        items.cogs,
        items.gross_margin,
        case when orders.order_status = 'delivered'
             then items.net_item_revenue + orders.shipping_fee else 0 end as recognized_revenue,
        case when orders.order_status = 'delivered'
             then items.gross_margin else 0 end                         as recognized_gross_margin,

        -- flags
        orders.order_status = 'delivered'                               as is_completed,
        orders.order_status = 'cancelled'                               as is_cancelled,
        orders.order_status = 'returned'                                as is_returned,
        coalesce(calendar.is_sale_day, false)                           as is_sale_day,
        orders.coupon_code is not null                                  as has_coupon,
        payments.is_split_payment,
        payments.is_cash_on_delivery,
        payments.used_emi,
        items.has_fashion_item,

        -- fulfilment
        orders.approved_at,
        orders.shipped_at,
        orders.delivered_at,
        orders.estimated_delivery_date,
        round(date_diff('minute', orders.purchased_at, orders.shipped_at) / 60.0, 1)
                                                                        as hours_to_ship,
        date_diff('day', orders.order_date, cast(orders.delivered_at as date))
                                                                        as delivery_days,
        date_diff('day', orders.estimated_delivery_date, cast(orders.delivered_at as date))
                                                                        as delivery_delay_days,
        case
            when orders.delivered_at is null then null
            else cast(orders.delivered_at as date) > orders.estimated_delivery_date
        end                                                             as is_delivered_late,

        -- voice of customer
        reviews.review_rating

    from orders
    left join items      on orders.order_id = items.order_id
    left join payments   on orders.order_id = payments.order_id
    left join sequenced  on orders.order_id = sequenced.order_id
    left join reviews    on orders.order_id = reviews.order_id
    left join calendar   on orders.order_date = calendar.date_day

)

select * from final
