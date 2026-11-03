with source as (

    select * from {{ source('shopflow', 'products') }}

)

select
    trim(product_id)                            as product_id,
    trim(product_name)                          as product_name,
    trim(category)                              as category,
    trim(sub_category)                          as sub_category,
    trim(brand)                                 as brand,
    trim(seller_id)                             as seller_id,
    {{ to_money('list_price') }}                as list_price,
    {{ to_money('cost_price') }}                as cost_price,
    cast(weight_grams as integer)               as weight_grams,
    upper(trim(is_active)) = 'Y'                as is_active,
    cast(created_at as timestamp)               as created_at,
    cast(updated_at as timestamp)               as updated_at,
    cast(_loaded_at as timestamp)               as loaded_at

from source
