{{
    config(
        materialized='table',
        alias='silver_lga_mapping'
    )
}}

select
    lga_name,
    suburb_name,
    -- Clean and standardize LGA names
    trim(upper(lga_name)) as lga_name_clean,
    -- Clean and standardize suburb names
    trim(upper(suburb_name)) as suburb_name_clean,
    -- Create a unique key for the mapping
    {{ dbt_utils.generate_surrogate_key(['lga_name', 'suburb_name']) }} as lga_suburb_key,
    current_timestamp as created_at,
    current_timestamp as updated_at
from {{ ref('bronze_lga_mapping') }}
where lga_name is not null
  and suburb_name is not null
  and trim(lga_name) != ''
  and trim(suburb_name) != ''
  -- Remove any duplicate entries
  and (lga_name, suburb_name) in (
    select lga_name, suburb_name
    from {{ ref('bronze_lga_mapping') }}
    where lga_name is not null
      and suburb_name is not null
      and trim(lga_name) != ''
      and trim(suburb_name) != ''
    group by lga_name, suburb_name
    having count(*) = 1
  )
