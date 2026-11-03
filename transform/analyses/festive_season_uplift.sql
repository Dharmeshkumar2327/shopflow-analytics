-- Ad-hoc analysis: how much does each sale event lift demand, and at what discount cost?
--
-- Baseline = the 28 non-sale days immediately BEFORE each event. Comparing against the
-- all-time average would be confounded by business growth (a 2025 normal day beats a
-- 2023 sale day), so each event gets its own local pre-period.
--
-- Run:  dbt compile -s festive_season_uplift   then execute target/compiled/.../festive_season_uplift.sql

with daily as (

    select
        order_date,
        count(*)                        as orders,
        sum(order_total)                as demand,          -- placed value incl. later returns
        sum(discount_amount)            as discounts,
        sum(gross_merchandise_value)    as gmv
    from {{ ref('fct_orders') }}
    where not is_cancelled
    group by 1

),

events as (

    select * from {{ ref('ref_sale_events') }}

),

during as (

    select
        events.event_name,
        events.event_type,
        count(*)                                        as days,
        avg(daily.orders)                               as avg_daily_orders,
        avg(daily.demand)                               as avg_daily_demand,
        sum(daily.discounts) / sum(daily.gmv)           as discount_rate
    from events
    inner join daily
        on daily.order_date between events.start_date and events.end_date
    group by 1, 2

),

pre_period as (

    select
        events.event_name,
        avg(daily.orders)                               as base_daily_orders,
        avg(daily.demand)                               as base_daily_demand,
        sum(daily.discounts) / sum(daily.gmv)           as base_discount_rate
    from events
    inner join daily
        on daily.order_date between events.start_date - 28 and events.start_date - 1
    where not exists (
        select 1 from events as other
        where daily.order_date between other.start_date and other.end_date
    )
    group by 1

)

select
    during.event_name,
    during.event_type,
    during.days,
    round(during.avg_daily_orders, 1)                                       as avg_daily_orders,
    round(pre_period.base_daily_orders, 1)                                  as baseline_daily_orders,
    round(during.avg_daily_orders / pre_period.base_daily_orders - 1, 3)    as order_uplift,
    round(during.avg_daily_demand / pre_period.base_daily_demand - 1, 3)    as demand_uplift,
    round(during.discount_rate, 3)                                          as discount_rate,
    round(pre_period.base_discount_rate, 3)                                 as baseline_discount_rate
from during
left join pre_period
    on during.event_name = pre_period.event_name
order by during.event_name
