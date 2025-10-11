{{
    config(
        materialized='table',
        alias='fact_listings'
    )
}}

select
    -- Fact table should only contain IDs and metrics
    listing_id,
    
    -- Foreign keys to dimensions
    host_id,
    {{ dbt_utils.generate_surrogate_key(['property_type_clean', 'room_type_clean', 'accommodates']) }} as property_key,
    {{ dbt_utils.generate_surrogate_key(['listing_neighbourhood_clean', 'host_neighbourhood_clean']) }} as neighbourhood_key,
    
    -- Metrics (as per assignment requirements)
    price_clean as price,
    has_availability_boolean as has_availability,
    availability_30,
    number_of_stays,
    estimated_revenue_30_days,
    
    -- Time dimensions
    scraped_date,
    scraped_year,
    scraped_month,
    scraped_day,
    
    -- Audit fields
    current_timestamp as created_at,
    current_timestamp as updated_at

from {{ ref('silver_airbnb_listings') }}
where listing_id is not null
  and host_id is not null
  and property_type_clean is not null
  and room_type_clean is not null
  and accommodates is not null
  and listing_neighbourhood_clean is not null
  and host_neighbourhood_clean is not null
  and scraped_date is not null
  and is_complete_record = true
