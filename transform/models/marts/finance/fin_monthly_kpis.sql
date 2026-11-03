-- Monthly business KPIs with MoM / YoY growth and fiscal-year-to-date revenue.

with orders as (

    select * from {{ ref('fct_orders') }}

),

monthly as (

    select
        order_month,
        any_value(fiscal_year)                                              as fiscal_year,
        count(*)                                                            as orders_placed,
        count(*) filter (where is_completed)                                as orders_completed,
        count(distinct customer_id)                                         as ordering_customers,
        count(*) filter (where is_first_order)                              as new_customers,
        sum(gross_merchandise_value) filter (where not is_cancelled)        as gmv,
        sum(discount_amount) filter (where not is_cancelled)                as discounts,
        sum(recognized_revenue)                                             as net_revenue,
        sum(recognized_gross_margin)                                        as gross_margin,
        count(*) filter (where is_cancelled)                                as cancelled_orders,
        count(*) filter (where is_returned)                                 as returned_orders,
        count(*) filter (where is_cash_on_delivery)                         as cod_orders,
        count(*) filter (where primary_payment_method = 'upi')              as upi_orders
    from orders
    group by order_month

),

ratios as (

    select
        *,
        {{ safe_divide('gross_margin', 'net_revenue') }}                    as gross_margin_pct,
        {{ safe_divide('net_revenue', 'orders_completed') }}                as avg_order_value,
        {{ safe_divide('discounts', 'gmv') }}                               as discount_rate,
        {{ safe_divide('cancelled_orders', 'orders_placed') }}              as cancellation_rate,
        {{ safe_divide('returned_orders', 'orders_completed + returned_orders') }}
                                                                            as return_rate,
        {{ safe_divide('orders_placed - new_customers', 'orders_placed') }}  as repeat_order_share,
        {{ safe_divide('cod_orders', 'orders_placed') }}                    as cod_share,
        {{ safe_divide('upi_orders', 'orders_placed') }}                    as upi_share
    from monthly

)

select
    *,
    lag(net_revenue, 1)  over (order by order_month)                        as net_revenue_prev_month,
    lag(net_revenue, 12) over (order by order_month)                        as net_revenue_same_month_last_year,
    {{ safe_divide('net_revenue - lag(net_revenue, 1) over (order by order_month)',
                   'lag(net_revenue, 1) over (order by order_month)') }}    as revenue_growth_mom,
    {{ safe_divide('net_revenue - lag(net_revenue, 12) over (order by order_month)',
                   'lag(net_revenue, 12) over (order by order_month)') }}   as revenue_growth_yoy,
    avg(net_revenue) over (
        order by order_month rows between 2 preceding and current row
    )                                                                       as net_revenue_3m_avg,
    sum(net_revenue) over (
        partition by fiscal_year order by order_month
        rows between unbounded preceding and current row
    )                                                                       as net_revenue_fytd

from ratios
order by order_month
