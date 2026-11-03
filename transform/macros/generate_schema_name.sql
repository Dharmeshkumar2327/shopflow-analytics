{#
    Use the custom schema name as-is (staging, core, finance ...) instead of dbt's
    default "<target_schema>_<custom_schema>". Keeps the warehouse layout clean:
    raw -> staging -> intermediate -> core / finance / marketing / operations
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
