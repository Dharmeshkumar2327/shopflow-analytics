-- Classic cohort retention matrix (rows = cohort, columns = month 0..12) for spreadsheets / slides.
select
    strftime(cohort_month, '%Y-%m') as cohort,
    any_value(cohort_size)          as customers
    {% for m in range(0, 13) %}
    , round(100 * max(case when months_since_first_order = {{ m }} then retention_rate end), 1) as m{{ m }}
    {% endfor %}
from {{ ref('mkt_customer_cohorts') }}
group by cohort_month
order by cohort_month
