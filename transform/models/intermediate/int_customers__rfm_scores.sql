-- Recency / Frequency / Monetary quintile scores (5 = best) for customers
-- with at least one completed order, as of var('as_of_date').

with customers as (

    select * from {{ ref('int_customers__order_history') }}
    where completed_orders > 0

),

base as (

    select
        customer_id,
        date_diff(
            'day',
            cast(last_completed_order_at as date),
            cast('{{ var("as_of_date") }}' as date)
        )                                   as recency_days,
        completed_orders                    as frequency,
        lifetime_revenue                    as monetary
    from customers

)

select
    customer_id,
    recency_days,
    frequency,
    monetary,
    ntile(5) over (order by recency_days desc, customer_id)    as r_score,
    ntile(5) over (order by frequency asc, customer_id)        as f_score,
    ntile(5) over (order by monetary asc, customer_id)         as m_score

from base
