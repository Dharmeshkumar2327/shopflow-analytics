with source as (

    select * from {{ source('shopflow', 'marketing_spend') }}

)

select
    {{ surrogate_key(['spend_date', 'channel']) }}     as spend_sk,
    cast(spend_date as date)                            as spend_date,
    {{ normalize_label('channel') }}                    as channel,
    {{ to_money('spend_inr') }}                         as spend_inr,
    cast(impressions as bigint)                         as impressions,
    cast(clicks as bigint)                              as clicks,
    cast(_loaded_at as timestamp)                       as loaded_at

from source
