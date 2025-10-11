{{
    config(
        materialized='table',
        alias='dim_host'
    )
}}

select
    host_id,
    host_neighbourhood,
    -- Add surrogate key for SCD Type 2
    {{ dbt_utils.generate_surrogate_key(['host_id', 'host_neighbourhood']) }} as host_surrogate_key,
    -- SCD Type 2 fields
    dbt_valid_from,
    dbt_valid_to,
    dbt_updated_at,
    current_timestamp as created_at
from {{ ref('dim_host_snapshot') }}
where dbt_valid_to is null  -- Only current records
  and host_id is not null
  and host_neighbourhood is not null
