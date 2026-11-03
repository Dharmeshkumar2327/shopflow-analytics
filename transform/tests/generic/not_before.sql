{#  Fails when column_name is earlier than other_column (e.g. shipped before it was purchased) #}
{% test not_before(model, column_name, other_column) %}
    select *
    from {{ model }}
    where {{ column_name }} < {{ other_column }}
{% endtest %}
