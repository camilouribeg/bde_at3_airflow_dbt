{{
    config(
        materialized='table',
        alias='silver_census_g01'
    )
}}

select
    lga_code_2016,
    tot_p_m as male_population,
    tot_p_f as female_population,
    (tot_p_m + tot_p_f) as total_population,
    round((tot_p_m::numeric / (tot_p_m + tot_p_f)) * 100, 2) as male_percentage,
    round((tot_p_f::numeric / (tot_p_m + tot_p_f)) * 100, 2) as female_percentage,
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('bronze_census_g01') }}
where lga_code_2016 is not null
  and tot_p_m is not null
  and tot_p_f is not null
  and (tot_p_m + tot_p_f) > 0
