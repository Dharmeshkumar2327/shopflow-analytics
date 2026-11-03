{#
    SCD Type 2 history of product pricing.
    Every `dbt snapshot` run compares list/cost price and active flag with the
    previous run and closes out the old row (dbt_valid_to) when anything changes -
    so price history is kept even though the source only stores current price.
#}
{% snapshot snap_products %}

{{
    config(
        target_schema = 'snapshots',
        unique_key = 'product_id',
        strategy = 'check',
        check_cols = ['list_price', 'cost_price', 'is_active']
    )
}}

select
    product_id,
    product_name,
    category,
    list_price,
    cost_price,
    is_active
from {{ ref('stg_shopflow__products') }}

{% endsnapshot %}
