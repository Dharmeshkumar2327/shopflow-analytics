with source as (

    select * from {{ source('shopflow', 'reviews') }}

)

select
    trim(review_id)                         as review_id,
    trim(order_id)                          as order_id,
    cast(rating as integer)                 as rating,
    cast(review_created_at as timestamp)    as review_created_at,
    cast(_loaded_at as timestamp)           as loaded_at

from source
