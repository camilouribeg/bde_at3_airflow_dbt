{{
    config(
        materialized='table',
        alias='dim_neighbourhood'
    )
}}

select
    neighbourhood_key,
    listing_neighbourhood,
    host_neighbourhood,
    -- Add surrogate key for SCD Type 2
    {{ dbt_utils.generate_surrogate_key(['neighbourhood_key', 'listing_neighbourhood', 'host_neighbourhood']) }} as neighbourhood_surrogate_key,
    -- SCD Type 2 fields
    dbt_valid_from,
    dbt_valid_to,
    dbt_updated_at,
    current_timestamp as created_at
from {{ ref('dim_neighbourhood_snapshot') }}
where dbt_valid_to is null  -- Only current records
  and neighbourhood_key is not null
  and listing_neighbourhood is not null
  and host_neighbourhood is not null
