-- Line items enriched with product attributes and unit economics (COGS, margin).

with items as (

    select * from {{ ref('stg_shopflow__order_items') }}

),

products as (

    select * from {{ ref('stg_shopflow__products') }}

)

select
    items.order_item_sk,
    items.order_id,
    items.order_item_id,
    items.product_id,
    items.seller_id,
    products.category,
    products.sub_category,
    products.brand,
    items.quantity,
    items.unit_price,
    items.gross_amount,
    items.discount_amount,
    items.net_amount,
    products.cost_price * items.quantity                        as cogs,
    items.net_amount - products.cost_price * items.quantity     as gross_margin

from items
left join products
    on items.product_id = products.product_id
