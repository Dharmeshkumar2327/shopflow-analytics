with source as (

    select * from {{ source('shopflow', 'sellers') }}

)

select
    trim(seller_id)                     as seller_id,
    trim(seller_name)                   as seller_name,
    {{ text_key('city') }}              as city_key,
    {{ text_key('state') }}             as state_key,
    cast(onboarded_at as timestamp)     as onboarded_at,
    cast(_loaded_at as timestamp)       as loaded_at

from source
