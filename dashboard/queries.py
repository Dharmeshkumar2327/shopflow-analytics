"""SQL used by the dashboard. Every query reads only from the dbt marts."""

MONTHLY_KPIS = """
    select order_month, fiscal_year, orders_placed, orders_completed, ordering_customers,
           new_customers, gmv, net_revenue, gross_margin, gross_margin_pct, avg_order_value,
           cancellation_rate, return_rate, cod_share, upi_share, net_revenue_3m_avg,
           revenue_growth_yoy
    from finance.fin_monthly_kpis
    order by order_month
"""

CATEGORY = """
    select fiscal_year, category, net_revenue, gross_margin, gross_margin_pct, return_rate
    from finance.fin_category_performance
"""

PAYMENT_MIX = """
    select k.order_month, k.fiscal_year, m.payment_method, m.order_share
    from finance.fin_payment_method_mix as m
    inner join finance.fin_monthly_kpis as k using (order_month)
    where m.payment_method in ('upi', 'cod', 'credit_card', 'debit_card')
    order by 1
"""

COHORTS = """
    select cohort_month, months_since_first_order, cohort_size, retention_rate,
           cumulative_revenue_per_customer
    from marketing.mkt_customer_cohorts
    where months_since_first_order <= 12
"""

RFM = """
    select rfm_segment, any_value(recommended_action) as recommended_action,
           count(*) as customers, sum(monetary) as lifetime_revenue,
           avg(recency_days) as avg_recency_days, avg(frequency) as avg_orders
    from marketing.mkt_rfm_segments
    group by rfm_segment
    order by customers desc
"""

LIFECYCLE = """
    select lifecycle_status, count(*) as customers
    from core.dim_customers
    group by 1
"""

CHANNELS = """
    select channel,
           sum(new_customers)                                   as new_customers,
           sum(spend)                                           as spend,
           sum(spend) / nullif(sum(new_customers), 0)           as cac,
           sum(ltv_180d_margin * new_customers) / sum(new_customers) as ltv_180d_margin,
           sum(ltv_180d_margin * new_customers) / nullif(sum(spend), 0) as ltv_to_cac
    from marketing.mkt_channel_performance
    where is_ltv_window_complete
    group by 1
    order by new_customers desc
"""

CHANNEL_TREND = """
    select cast(date_trunc('quarter', month) as date) as quarter, channel,
           sum(ltv_180d_margin * new_customers) / nullif(sum(spend), 0) as ltv_to_cac
    from marketing.mkt_channel_performance
    where is_paid_channel and is_ltv_window_complete
    group by 1, 2
    order by 1
"""

DELIVERY_TREND = """
    select order_month, city_tier,
           sum(on_time_rate * delivered_orders) / sum(delivered_orders) as on_time_rate
    from operations.ops_delivery_performance
    group by 1, 2
    order by 1
"""

DELIVERY_RATING = """
    select city_tier,
           sum(avg_rating_on_time * reviews) / sum(reviews)  as rating_when_on_time,
           sum(avg_rating_late * reviews) / sum(reviews)     as rating_when_late,
           sum(avg_delivery_days * delivered_orders) / sum(delivered_orders) as avg_delivery_days
    from operations.ops_delivery_performance
    group by 1
    order by 1
"""

SELLERS = """
    select seller_name, region, seller_tier, orders, net_revenue, on_time_rate,
           cancellation_rate, return_rate, avg_rating, seller_score
    from operations.ops_seller_scorecard
    order by revenue_rank
"""
