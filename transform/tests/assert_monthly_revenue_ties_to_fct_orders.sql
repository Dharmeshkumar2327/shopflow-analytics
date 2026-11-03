-- The executive KPI table must tie out to the order fact table to the rupee.
with kpis as (
    select sum(net_revenue) as revenue from {{ ref('fin_monthly_kpis') }}
),
orders as (
    select sum(recognized_revenue) as revenue from {{ ref('fct_orders') }}
)
select kpis.revenue as kpi_revenue, orders.revenue as order_revenue
from kpis cross join orders
where abs(kpis.revenue - orders.revenue) > 1
