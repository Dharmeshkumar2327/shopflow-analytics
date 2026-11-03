with source as (

    select * from {{ source('shopflow', 'customers') }}

),

renamed as (

    select
        trim(customer_id)                                   as customer_id,
        lower(trim(email))                                  as email,
        split_part(lower(trim(email)), '@', 2)              as email_domain,
        {{ text_key('city') }}                              as city_key,
        {{ text_key('state') }}                             as state_key,
        cast(signup_date as date)                           as signup_date,
        {{ normalize_label('acquisition_channel') }}        as acquisition_channel,
        cast(_loaded_at as timestamp)                       as loaded_at

    from source

),

-- The source re-extracts customers when their profile changes.
-- Keep only the latest version of each customer.
deduplicated as (

    select *
    from renamed
    qualify row_number() over (
        partition by customer_id
        order by loaded_at desc
    ) = 1

)

select * from deduplicated
