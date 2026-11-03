with source as (

    select * from {{ source('shopflow', 'order_items') }}

),

typed as (

    select
        trim(order_id)                          as order_id,
        cast(order_item_id as integer)          as order_item_id,
        trim(product_id)                        as product_id,
        trim(seller_id)                         as seller_id,
        cast(quantity as integer)               as quantity,
        {{ to_money('unit_price') }}            as unit_price,
        {{ to_money('discount_amount') }}       as discount_amount,
        cast(_loaded_at as timestamp)           as loaded_at

    from source

)

select
    {{ surrogate_key(['order_id', 'order_item_id']) }}     as order_item_sk,
    order_id,
    order_item_id,
    product_id,
    seller_id,
    quantity,
    unit_price,
    discount_amount,
    unit_price * quantity                                   as gross_amount,
    unit_price * quantity - discount_amount                 as net_amount,
    loaded_at

from typed
