{{
    config(
        materialized='table',
        alias='silver_census_g02'
    )
}}

select
    lga_code_2016,
    median_age_persons,
    median_mortgage_repay_monthly,
    median_tot_hhd_inc_weekly,
    -- Calculate annual mortgage repayment
    (median_mortgage_repay_monthly * 12) as median_mortgage_repay_annual,
    -- Calculate annual household income
    (median_tot_hhd_inc_weekly * 52) as median_tot_hhd_inc_annual,
    -- Calculate mortgage to income ratio
    case 
        when median_tot_hhd_inc_weekly > 0 then
            round((median_mortgage_repay_monthly * 12)::numeric / (median_tot_hhd_inc_weekly * 52) * 100, 2)
        else null
    end as mortgage_to_income_ratio_pct,
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('bronze_census_g02') }}
where lga_code_2016 is not null
  and median_age_persons is not null
  and median_mortgage_repay_monthly is not null
  and median_tot_hhd_inc_weekly is not null
  and median_age_persons > 0
  and median_mortgage_repay_monthly >= 0
  and median_tot_hhd_inc_weekly > 0
