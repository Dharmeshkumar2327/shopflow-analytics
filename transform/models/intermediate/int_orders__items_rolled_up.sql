-- Order-grain summary of line items.

select
    order_id,
    count(*)                                        as line_count,
    sum(quantity)                                   as units,
    sum(gross_amount)                               as gross_merchandise_value,
    sum(discount_amount)                            as discount_amount,
    sum(net_amount)                                 as net_item_revenue,
    sum(cogs)                                       as cogs,
    sum(gross_margin)                               as gross_margin,
    count(distinct seller_id)                       as distinct_sellers,
    arg_max(category, net_amount)                   as primary_category,
    arg_min(seller_id, order_item_id)               as primary_seller_id,
    bool_or(category = 'Fashion')                   as has_fashion_item

from {{ ref('int_order_items__enriched') }}
group by order_id
