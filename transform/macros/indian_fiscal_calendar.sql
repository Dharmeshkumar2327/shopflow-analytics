{#
    Indian financial year runs 1 April -> 31 March.
    e.g. 2024-05-10 -> 'FY2024-25', fiscal quarter 1 (Apr-Jun)
#}
{% macro fiscal_year_start(date_column) -%}
    case when month({{ date_column }}) >= 4
         then year({{ date_column }})
         else year({{ date_column }}) - 1
    end
{%- endmacro %}

{% macro indian_fiscal_year(date_column) -%}
    'FY' || cast({{ fiscal_year_start(date_column) }} as varchar)
         || '-' || right(cast({{ fiscal_year_start(date_column) }} + 1 as varchar), 2)
{%- endmacro %}

{% macro indian_fiscal_quarter(date_column) -%}
    cast(floor(((month({{ date_column }}) + 8) % 12) / 3) + 1 as integer)
{%- endmacro %}
