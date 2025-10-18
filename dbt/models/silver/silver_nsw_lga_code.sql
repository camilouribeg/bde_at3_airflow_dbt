{{
    config(
        materialized='table',
        alias='silver_nsw_lga_code'
    )
}}

select
    lga_code,
    lga_name,
    -- Clean and standardize LGA codes
    trim(upper(lga_code)) as lga_code_clean,
    -- Clean and standardize LGA names
    trim(upper(lga_name)) as lga_name_clean,
    -- Create a unique key
    {{ dbt_utils.generate_surrogate_key(['lga_code', 'lga_name']) }} as lga_code_key,
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('bronze_nsw_lga_code') }}
where lga_code is not null
  and lga_name is not null
  and trim(lga_code) != ''
  and trim(lga_name) != ''
  -- Remove any duplicate entries
  and (lga_code, lga_name) in (
    select lga_code, lga_name
    from {{ ref('bronze_nsw_lga_code') }}
    where lga_code is not null
      and lga_name is not null
      and trim(lga_code) != ''
      and trim(lga_name) != ''
    group by lga_code, lga_name
    having count(*) = 1
  )
