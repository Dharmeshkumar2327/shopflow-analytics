-- Maps RFM scores to actionable CRM segments.
-- Rule order matters: the first matching rule wins.

with scores as (

    select * from {{ ref('int_customers__rfm_scores') }}

)

select
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    cast(r_score as varchar) || cast(f_score as varchar) || cast(m_score as varchar)
                                                            as rfm_cell,
    case
        when r_score >= 4 and f_score >= 4                  then 'Champions'
        when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'Cannot Lose Them'
        when r_score >= 3 and f_score >= 3                  then 'Loyal'
        when r_score >= 4 and f_score <= 1                  then 'New Customers'
        when r_score >= 4                                   then 'Potential Loyalists'
        when r_score = 3                                    then 'Need Attention'
        when f_score >= 3                                   then 'At Risk'
        else 'Hibernating'
    end                                                     as rfm_segment,
    case
        when r_score >= 4 and f_score >= 4                  then 'Reward: early access to sales, referral programme'
        when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'Win back now: personal outreach + high-value offer'
        when r_score >= 3 and f_score >= 3                  then 'Upsell: loyalty tier, bundles'
        when r_score >= 4 and f_score <= 1                  then 'Onboard: second-order coupon within 30 days'
        when r_score >= 4                                   then 'Nurture: category recommendations'
        when r_score = 3                                    then 'Re-engage: limited-time offer'
        when f_score >= 3                                   then 'Reactivate: festive-sale reminder'
        else 'Low-cost reactivation only'
    end                                                     as recommended_action

from scores
