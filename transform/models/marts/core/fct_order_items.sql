{{
    config(
        materialized = 'incremental',
        unique_key = 'order_item_sk',
        incremental_strategy = 'delete+insert',
        on_schema_change = 'append_new_columns'
    )
}}

-- Line-item fact for product, category, brand and seller analysis.
-- Incremental: only re-processes orders placed in the last 3 days of loaded data
-- (look-back window catches late status changes) instead of rebuilding history.

with items as (

    select * from {{ ref('int_order_items__enriched') }}

),

orders as (

    select order_id, customer_id, purchased_at, order_date, order_status
    from {{ ref('stg_shopflow__orders') }}

    {% if is_incremental() %}
    where purchased_at >= (select max(purchased_at) - interval 3 day from {{ this }})
    {% endif %}

)

select
    items.order_item_sk,
    items.order_id,
    items.order_item_id,
    orders.customer_id,
    items.product_id,
    items.seller_id,
    orders.purchased_at,
    orders.order_date,
    cast(date_trunc('month', orders.order_date) as date)       as order_month,
    orders.order_status,
    items.category,
    items.sub_category,
    items.brand,
    items.quantity,
    items.unit_price,
    items.gross_amount,
    items.discount_amount,
    items.net_amount,
    items.cogs,
    items.gross_margin,
    {{ safe_divide('items.discount_amount', 'items.gross_amount') }}   as discount_rate,
    case when orders.order_status = 'delivered'
         then items.net_amount else 0 end                       as recognized_revenue,
    case when orders.order_status = 'delivered'
         then items.gross_margin else 0 end                     as recognized_gross_margin

from items
inner join orders
    on items.order_id = orders.order_id
