{{
    config(
        materialized='table',
        alias='dim_lga'
    )
}}

select
    lga_code_2016,
    male_population,
    female_population,
    total_population,
    male_percentage,
    female_percentage,
    -- Add surrogate key for SCD Type 2
    {{ dbt_utils.generate_surrogate_key(['lga_code_2016', 'total_population']) }} as lga_surrogate_key,
    -- SCD Type 2 fields
    dbt_valid_from,
    dbt_valid_to,
    dbt_updated_at,
    current_timestamp as created_at
from {{ ref('dim_lga_snapshot') }}
where dbt_valid_to is null  -- Only current records
  and lga_code_2016 is not null
  and total_population > 0
