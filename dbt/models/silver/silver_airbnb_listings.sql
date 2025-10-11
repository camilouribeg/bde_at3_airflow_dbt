{{
    config(
        materialized='table',
        alias='silver_airbnb_listings'
    )
}}

select
    -- Core identifiers
    listing_id,
    host_id,
    
    -- Location data (cleaned)
    trim(upper(listing_neighbourhood)) as listing_neighbourhood_clean,
    trim(upper(host_neighbourhood)) as host_neighbourhood_clean,
    
    -- Property characteristics (cleaned)
    trim(upper(property_type)) as property_type_clean,
    trim(upper(room_type)) as room_type_clean,
    accommodates,
    
    -- Availability and pricing
    case 
        when has_availability = 't' then true
        when has_availability = 'f' then false
        else null
    end as has_availability_boolean,
    availability_30,
    
    -- Price cleaning and validation
    case 
        when price is not null and price > 0 then price
        else null
    end as price_clean,
    
    -- Date handling
    scraped_date,
    extract(year from scraped_date) as scraped_year,
    extract(month from scraped_date) as scraped_month,
    extract(day from scraped_date) as scraped_day,
    
    -- Business logic calculations
    case 
        when has_availability = 't' and availability_30 is not null then
            (30 - availability_30)
        else 0
    end as number_of_stays,
    
    -- Estimated revenue calculation (for active listings only)
    case 
        when has_availability = 't' 
         and price is not null 
         and price > 0 
         and availability_30 is not null then
            price * (30 - availability_30)
        else 0
    end as estimated_revenue_30_days,
    
    -- Data quality flags
    case 
        when listing_id is not null 
         and host_id is not null 
         and property_type is not null 
         and room_type is not null 
         and accommodates is not null 
         and scraped_date is not null then true
        else false
    end as is_complete_record,
    
    current_timestamp as created_at,
    current_timestamp as updated_at

from {{ ref('bronze_airbnb_listings') }}
where listing_id is not null
  and host_id is not null
  and scraped_date is not null
  and property_type is not null
  and room_type is not null
  and accommodates is not null
  and accommodates > 0
  and scraped_date >= '2020-01-01'
  and scraped_date <= '2021-12-31'
