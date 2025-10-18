{{
    config(
        materialized='table',
        alias='silver_airbnb_listings'
    )
}}

select
    -- Core identifiers
    listing_id,
    scrape_id,
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
        when price is not null and price != '' and price::numeric > 0 then price::numeric
        else null
    end as price_clean,
    
    -- Date handling
    scraped_date,
    case 
        when scraped_date ~ '^\d{4}-\d{2}-\d{2}$' then scraped_date::date
        else null
    end as scraped_date_clean,
    
    -- Host information
    host_name,
    host_since,
    case 
        when host_is_superhost = 't' then true
        when host_is_superhost = 'f' then false
        when host_is_superhost is null or host_is_superhost = '' then null
        else null
    end as host_is_superhost_boolean,
    
    -- Review scores (convert to numeric)
    case 
        when review_scores_rating is not null and review_scores_rating != '' then review_scores_rating::numeric
        else null
    end as review_scores_rating_clean,
    
    case 
        when review_scores_accuracy is not null and review_scores_accuracy != '' then review_scores_accuracy::numeric
        else null
    end as review_scores_accuracy_clean,
    
    case 
        when review_scores_cleanliness is not null and review_scores_cleanliness != '' then review_scores_cleanliness::numeric
        else null
    end as review_scores_cleanliness_clean,
    
    case 
        when review_scores_checkin is not null and review_scores_checkin != '' then review_scores_checkin::numeric
        else null
    end as review_scores_checkin_clean,
    
    case 
        when review_scores_communication is not null and review_scores_communication != '' then review_scores_communication::numeric
        else null
    end as review_scores_communication_clean,
    
    case 
        when review_scores_value is not null and review_scores_value != '' then review_scores_value::numeric
        else null
    end as review_scores_value_clean,
    
    -- Business logic calculations
    case 
        when has_availability = 't' and availability_30 is not null and availability_30 != '' then
            (30 - availability_30::integer)
        else 0
    end as number_of_stays,
    
    -- Estimated revenue calculation (for active listings only)
    case 
        when has_availability = 't' 
         and price is not null 
         and price != ''
         and price::numeric > 0 
         and availability_30 is not null 
         and availability_30 != '' then
            price::numeric * (30 - availability_30::integer)
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
  and accommodates != ''
  and scraped_date >= '2020-01-01'
  and scraped_date <= '2021-12-31'
