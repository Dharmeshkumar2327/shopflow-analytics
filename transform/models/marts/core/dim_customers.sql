with customers as (

    select * from {{ ref('stg_shopflow__customers') }}

),

history as (

    select * from {{ ref('int_customers__order_history') }}

),

cities as (

    select * from {{ ref('ref_city_tiers') }}

),

states as (

    select * from {{ ref('ref_indian_states') }}

),

joined as (

    select
        customers.customer_id,
        customers.email_domain,
        coalesce(cities.city, customers.city_key)                   as city,
        coalesce(states.state, customers.state_key)                 as state,
        states.state_code,
        coalesce(states.region, 'Unknown')                          as region,
        coalesce(cities.city_tier, 'Unclassified')                  as city_tier,
        customers.acquisition_channel,
        customers.signup_date,
        cast(date_trunc('month', customers.signup_date) as date)    as signup_month,

        cast(history.first_order_at as date)                        as first_order_date,
        cast(history.last_order_at as date)                         as last_order_date,
        cast(date_trunc('month', history.first_order_at) as date)   as cohort_month,
        date_diff('day', customers.signup_date,
                  cast(history.first_order_at as date))             as days_to_first_order,

        coalesce(history.total_orders, 0)                           as total_orders,
        coalesce(history.completed_orders, 0)                       as completed_orders,
        coalesce(history.cancelled_orders, 0)                       as cancelled_orders,
        coalesce(history.returned_orders, 0)                        as returned_orders,
        coalesce(history.lifetime_revenue, 0)                       as lifetime_revenue,
        coalesce(history.lifetime_gross_margin, 0)                  as lifetime_gross_margin,
        {{ safe_divide('history.lifetime_revenue',
                       'history.completed_orders') }}               as avg_order_value,
        date_diff('day', cast(history.last_order_at as date),
                  cast('{{ var("as_of_date") }}' as date))          as days_since_last_order

    from customers
    left join history
        on customers.customer_id = history.customer_id
    left join cities
        on customers.city_key = lower(cities.city)
    left join states
        on customers.state_key = lower(states.state)

)

select
    *,
    completed_orders > 1                                            as is_repeat_customer,
    case
        when total_orders = 0                                           then 'never_purchased'
        when days_since_last_order > {{ var('churned_after_days') }}    then 'churned'
        when days_since_last_order > {{ var('at_risk_after_days') }}    then 'at_risk'
        else 'active'
    end                                                             as lifecycle_status

from joined
