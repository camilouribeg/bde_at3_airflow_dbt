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
    
    -- Time dimensions (extract from scraped_date_clean)
    scraped_date_clean as scraped_date,
    extract(year from scraped_date_clean) as scraped_year,
    extract(month from scraped_date_clean) as scraped_month,
    extract(day from scraped_date_clean) as scraped_day,
    
    -- Additional metrics for mart views
    host_is_superhost_boolean as host_is_superhost,
    review_scores_rating_clean as review_scores_rating,
    
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
  and scraped_date_clean is not null
  and is_complete_record = true
