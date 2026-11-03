-- Category P&L by fiscal year: where the revenue AND the margin come from.

with items as (

    select * from {{ ref('fct_order_items') }}

),

calendar as (

    select date_day, fiscal_year from {{ ref('dim_date') }}

)

select
    calendar.fiscal_year,
    items.category,
    count(distinct items.order_id)                                      as orders,
    sum(items.quantity)                                                 as units,
    sum(items.gross_amount) filter (where items.order_status <> 'cancelled')
                                                                        as gmv,
    sum(items.recognized_revenue)                                       as net_revenue,
    sum(items.recognized_gross_margin)                                  as gross_margin,
    {{ safe_divide('sum(items.recognized_gross_margin)', 'sum(items.recognized_revenue)') }}
                                                                        as gross_margin_pct,
    {{ safe_divide("count(distinct items.order_id) filter (where items.order_status = 'returned')",
                   "count(distinct items.order_id) filter (where items.order_status in ('delivered', 'returned'))") }}
                                                                        as return_rate,
    {{ safe_divide('sum(items.discount_amount)', 'sum(items.gross_amount)') }}
                                                                        as avg_discount_rate

from items
inner join calendar
    on items.order_date = calendar.date_day
group by 1, 2
