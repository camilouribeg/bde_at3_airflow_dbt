{{
    config(
        materialized='table',
        alias='dim_suburb'
    )
}}

select
    suburb_name_clean as suburb_name,
    lga_name_clean as lga_name,
    lga_suburb_key,
    -- Add surrogate key for joining
    {{ dbt_utils.generate_surrogate_key(['suburb_name_clean', 'lga_name_clean']) }} as suburb_surrogate_key,
    -- Audit fields
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('silver_lga_mapping') }}
where suburb_name_clean is not null
  and lga_name_clean is not null
  and suburb_name_clean <> ''
  and lga_name_clean <> ''
