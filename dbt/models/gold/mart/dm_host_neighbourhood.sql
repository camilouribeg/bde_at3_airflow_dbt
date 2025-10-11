{{
    config(
        materialized='view',
        alias='dm_host_neighbourhood'
    )
}}

with fact_with_dimensions as (
    select
        f.listing_id,
        f.scraped_date,
        f.scraped_year,
        f.scraped_month,
        f.host_id,
        f.estimated_revenue_30_days,
        -- Get host neighbourhood from Silver data
        s.host_neighbourhood_clean as host_neighbourhood,
        -- Get LGA mapping to convert host_neighbourhood to LGA
        lga.lga_name as host_neighbourhood_lga
    from {{ ref('fact_listings') }} f
    left join {{ ref('silver_airbnb_listings') }} s
        on f.listing_id = s.listing_id
    left join {{ ref('silver_lga_mapping') }} lga
        on s.host_neighbourhood_clean = lga.suburb_name_clean
),

monthly_metrics as (
    select
        host_neighbourhood_lga,
        scraped_year,
        scraped_month,
        -- Number of distinct hosts
        count(distinct host_id) as distinct_hosts,
        -- Total estimated revenue (sum of all listings' revenue)
        sum(estimated_revenue_30_days) as total_estimated_revenue,
        -- Estimated revenue per host (distinct)
        round(
            (sum(estimated_revenue_30_days)::numeric / count(distinct host_id)), 
            2
        ) as estimated_revenue_per_host
    from fact_with_dimensions
    where host_neighbourhood_lga is not null
      and host_id is not null
    group by host_neighbourhood_lga, scraped_year, scraped_month
)

select
    host_neighbourhood_lga,
    scraped_year,
    scraped_month,
    distinct_hosts,
    total_estimated_revenue,
    estimated_revenue_per_host
from monthly_metrics
order by host_neighbourhood_lga, scraped_year, scraped_month
