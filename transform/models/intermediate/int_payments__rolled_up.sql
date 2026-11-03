-- Order-grain summary of payments (handles split tenders such as wallet + UPI).

select
    order_id,
    count(*)                                        as payment_count,
    sum(amount)                                     as payment_total,
    -- method that covered the largest share of the order
    arg_max(payment_method, amount)                 as primary_payment_method,
    count(*) > 1                                    as is_split_payment,
    bool_or(payment_method = 'cod')                 as is_cash_on_delivery,
    bool_or(payment_method = 'emi')                 as used_emi,
    max(installments)                               as max_installments,
    arg_min(payment_status, payment_sequence)       as payment_status

from {{ ref('stg_shopflow__payments') }}
group by order_id
