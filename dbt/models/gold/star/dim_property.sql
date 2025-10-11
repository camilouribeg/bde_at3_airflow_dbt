{{
    config(
        materialized='table',
        alias='dim_property'
    )
}}

select
    property_key,
    property_type,
    room_type,
    accommodates,
    -- Add surrogate key for SCD Type 2
    {{ dbt_utils.generate_surrogate_key(['property_key', 'property_type', 'room_type', 'accommodates']) }} as property_surrogate_key,
    -- SCD Type 2 fields
    dbt_valid_from,
    dbt_valid_to,
    dbt_updated_at,
    current_timestamp as created_at
from {{ ref('dim_property_snapshot') }}
where dbt_valid_to is null  -- Only current records
  and property_key is not null
  and property_type is not null
  and room_type is not null
  and accommodates is not null
