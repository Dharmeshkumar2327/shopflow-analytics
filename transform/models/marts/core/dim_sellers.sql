with sellers as (

    select * from {{ ref('stg_shopflow__sellers') }}

),

cities as (

    select * from {{ ref('ref_city_tiers') }}

),

states as (

    select * from {{ ref('ref_indian_states') }}

)

select
    sellers.seller_id,
    sellers.seller_name,
    coalesce(cities.city, sellers.city_key)                     as city,
    coalesce(states.state, sellers.state_key)                   as state,
    coalesce(states.region, 'Unknown')                          as region,
    coalesce(cities.city_tier, 'Unclassified')                  as city_tier,
    cast(sellers.onboarded_at as date)                          as onboarded_date,
    date_diff('month', cast(sellers.onboarded_at as date),
              cast('{{ var("as_of_date") }}' as date))          as tenure_months

from sellers
left join cities
    on sellers.city_key = lower(cities.city)
left join states
    on sellers.state_key = lower(states.state)
