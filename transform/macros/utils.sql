{# Normalise free-text labels: '  Credit Card' / 'CREDIT-CARD' -> 'credit_card' #}
{% macro normalize_label(column) -%}
    lower(regexp_replace(trim({{ column }}), '[\s\-]+', '_', 'g'))
{%- endmacro %}

{# Lookup key for joining hand-keyed text to reference data #}
{% macro text_key(column) -%}
    lower(trim({{ column }}))
{%- endmacro %}

{# Division that returns NULL instead of erroring / exploding on zero #}
{% macro safe_divide(numerator, denominator) -%}
    ({{ numerator }}) / nullif(({{ denominator }}), 0)
{%- endmacro %}

{# Deterministic surrogate key from one or more columns #}
{% macro surrogate_key(columns) -%}
    md5(concat_ws('||'
    {%- for col in columns %}, coalesce(cast({{ col }} as varchar), '_null_'){% endfor -%}
    ))
{%- endmacro %}

{# Cast raw text money columns (all raw data lands as VARCHAR) #}
{% macro to_money(column) -%}
    cast(nullif(trim({{ column }}), '') as decimal(14, 2))
{%- endmacro %}
