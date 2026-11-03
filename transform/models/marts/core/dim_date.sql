-- Calendar dimension with Indian fiscal calendar and marketplace sale events.

with spine as (

    select cast(range as date) as date_day
    from range(
        cast('{{ var("date_spine_start") }}' as date),
        cast('{{ var("date_spine_end") }}' as date) + interval 1 day,
        interval 1 day
    )

),

sale_events as (

    select * from {{ ref('ref_sale_events') }}

)

select
    spine.date_day,
    year(spine.date_day)                                    as calendar_year,
    quarter(spine.date_day)                                 as calendar_quarter,
    month(spine.date_day)                                   as month_number,
    strftime(spine.date_day, '%b')                          as month_short_name,
    cast(date_trunc('month', spine.date_day) as date)       as month_start,
    cast(date_trunc('week', spine.date_day) as date)        as week_start,
    isodow(spine.date_day)                                  as iso_day_of_week,
    strftime(spine.date_day, '%A')                          as day_name,
    isodow(spine.date_day) in (6, 7)                        as is_weekend,
    {{ indian_fiscal_year('spine.date_day') }}              as fiscal_year,
    {{ indian_fiscal_quarter('spine.date_day') }}           as fiscal_quarter,
    sale_events.event_name                                  as sale_event_name,
    sale_events.event_type                                  as sale_event_type,
    sale_events.event_name is not null                      as is_sale_day

from spine
left join sale_events
    on spine.date_day between sale_events.start_date and sale_events.end_date
