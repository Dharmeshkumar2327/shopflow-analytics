-- Unit economics by acquisition channel and month:
-- spend -> new customers -> CAC -> 180-day value -> LTV:CAC.

with customers as (

    select customer_id, acquisition_channel, cohort_month, first_order_date
    from {{ ref('dim_customers') }}
    where first_order_date is not null

),

-- value each new customer generated within the LTV window after their first order
customer_value as (

    select
        customers.customer_id,
        customers.acquisition_channel,
        customers.cohort_month,
        sum(orders.recognized_revenue)          as revenue_in_window,
        sum(orders.recognized_gross_margin)     as margin_in_window
    from customers
    left join {{ ref('fct_orders') }} as orders
        on  customers.customer_id = orders.customer_id
        and orders.order_date < customers.first_order_date + {{ var('ltv_window_days') }}
    group by 1, 2, 3

),

acquisition as (

    select
        cohort_month                            as month,
        acquisition_channel                     as channel,
        count(*)                                as new_customers,
        sum(revenue_in_window)                  as ltv_revenue,
        sum(margin_in_window)                   as ltv_margin
    from customer_value
    group by 1, 2

),

spend as (

    select
        cast(date_trunc('month', spend_date) as date)   as month,
        channel,
        sum(spend_inr)                                  as spend,
        sum(impressions)                                as impressions,
        sum(clicks)                                     as clicks
    from {{ ref('stg_shopflow__marketing_spend') }}
    group by 1, 2

)

select
    acquisition.month,
    acquisition.channel,
    acquisition.channel in ('paid_search', 'social', 'affiliate', 'email')
                                                                    as is_paid_channel,
    acquisition.new_customers,
    coalesce(spend.spend, 0)                                        as spend,
    spend.impressions,
    spend.clicks,
    {{ safe_divide('spend.spend', 'acquisition.new_customers') }}   as cac,
    {{ safe_divide('acquisition.ltv_revenue', 'acquisition.new_customers') }}
                                                                    as ltv_180d_revenue,
    {{ safe_divide('acquisition.ltv_margin', 'acquisition.new_customers') }}
                                                                    as ltv_180d_margin,
    {{ safe_divide('acquisition.ltv_margin', 'spend.spend') }}      as ltv_to_cac,
    -- only cohorts that have had the full window to mature should be compared
    -- (the cohort's LAST customer also needs the full window, hence + 1 month)
    cast(acquisition.month + interval 1 month as date) + {{ var('ltv_window_days') }}
        <= cast('{{ var("as_of_date") }}' as date)                  as is_ltv_window_complete

from acquisition
left join spend
    on  acquisition.month = spend.month
    and acquisition.channel = spend.channel
