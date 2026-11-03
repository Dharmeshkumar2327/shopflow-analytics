-- Monthly acquisition cohorts: retention curve and cumulative revenue per customer (LTV curve).
-- A customer is 'retained' in a month if they placed any order in it;
-- revenue counts recognised (delivered) revenue only.

with customers as (

    select customer_id, cohort_month
    from {{ ref('dim_customers') }}
    where cohort_month is not null

),

activity as (

    select
        orders.customer_id,
        customers.cohort_month,
        date_diff('month', customers.cohort_month, orders.order_month)  as months_since_first_order,
        orders.recognized_revenue
    from {{ ref('fct_orders') }} as orders
    inner join customers
        on orders.customer_id = customers.customer_id

),

cohort_sizes as (

    select cohort_month, count(*) as cohort_size
    from customers
    group by cohort_month

),

cohort_activity as (

    select
        cohort_month,
        months_since_first_order,
        count(distinct customer_id)     as active_customers,
        sum(recognized_revenue)         as revenue
    from activity
    group by 1, 2

)

select
    cohort_activity.cohort_month,
    cohort_activity.months_since_first_order,
    cohort_sizes.cohort_size,
    cohort_activity.active_customers,
    {{ safe_divide('cohort_activity.active_customers', 'cohort_sizes.cohort_size') }}
                                                                    as retention_rate,
    cohort_activity.revenue,
    {{ safe_divide(
        'sum(cohort_activity.revenue) over (
            partition by cohort_activity.cohort_month
            order by cohort_activity.months_since_first_order
            rows between unbounded preceding and current row)',
        'cohort_sizes.cohort_size') }}                              as cumulative_revenue_per_customer

from cohort_activity
inner join cohort_sizes
    on cohort_activity.cohort_month = cohort_sizes.cohort_month
