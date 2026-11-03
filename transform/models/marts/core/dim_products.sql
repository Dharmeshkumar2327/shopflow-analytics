with products as (

    select * from {{ ref('stg_shopflow__products') }}

),

sellers as (

    select seller_id, seller_name from {{ ref('stg_shopflow__sellers') }}

)

select
    products.product_id,
    products.product_name,
    products.category,
    products.sub_category,
    products.brand,
    products.seller_id,
    sellers.seller_name,
    products.list_price,
    products.cost_price,
    {{ safe_divide('products.list_price - products.cost_price', 'products.list_price') }}
                                                        as list_margin_pct,
    case
        when products.list_price < 500   then '1. Under 500'
        when products.list_price < 2000  then '2. 500 - 1,999'
        when products.list_price < 10000 then '3. 2,000 - 9,999'
        else '4. 10,000+'
    end                                                 as price_band,
    products.weight_grams,
    products.is_active,
    cast(products.created_at as date)                   as listed_date

from products
left join sellers
    on products.seller_id = sellers.seller_id
