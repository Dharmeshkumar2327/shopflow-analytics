with source as (

    select * from {{ source('shopflow', 'payments') }}

),

typed as (

    select
        trim(payment_id)                            as payment_id,
        trim(order_id)                              as order_id,
        cast(payment_sequence as integer)           as payment_sequence,
        {{ normalize_label('payment_method') }}     as payment_method_raw,
        {{ normalize_label('payment_status') }}     as payment_status,
        {{ to_money('amount') }}                    as amount,
        cast(installments as integer)               as installments,
        cast(paid_at as timestamp)                  as paid_at,
        cast(_loaded_at as timestamp)               as loaded_at

    from source

)

select
    payment_id,
    order_id,
    payment_sequence,
    -- the checkout service, mobile app and COD courier all label methods differently
    case payment_method_raw
        when 'cash_on_delivery' then 'cod'
        when 'net_banking'      then 'netbanking'
        else payment_method_raw
    end                                             as payment_method,
    payment_status,
    amount,
    installments,
    paid_at,
    loaded_at

from typed
