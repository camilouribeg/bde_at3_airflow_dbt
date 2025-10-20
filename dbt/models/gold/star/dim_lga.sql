{{
    config(
        materialized='table',
        alias='dim_lga'
    )
}}

select
    lga_code,
    lga_name,
    -- Add surrogate key for joining
    {{ dbt_utils.generate_surrogate_key(['lga_code']) }} as lga_surrogate_key,
    -- Audit fields
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('silver_nsw_lga_code') }}
where lga_code is not null
  and lga_name is not null
