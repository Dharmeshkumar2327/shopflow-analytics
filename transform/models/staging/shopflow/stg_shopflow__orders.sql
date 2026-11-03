with source as (

    select * from {{ source('shopflow', 'orders') }}

)

select
    trim(order_id)                                      as order_id,
    trim(customer_id)                                   as customer_id,
    {{ normalize_label('order_status') }}               as order_status,
    {{ normalize_label('order_channel') }}              as order_channel,
    cast(purchased_at as timestamp)                     as purchased_at,
    cast(purchased_at as date)                          as order_date,
    cast(approved_at as timestamp)                      as approved_at,
    cast(shipped_at as timestamp)                       as shipped_at,
    cast(delivered_at as timestamp)                     as delivered_at,
    cast(estimated_delivery_date as date)               as estimated_delivery_date,
    {{ to_money('shipping_fee') }}                      as shipping_fee,
    nullif(upper(trim(coupon_code)), '')                as coupon_code,
    cast(_loaded_at as timestamp)                       as loaded_at

from source
