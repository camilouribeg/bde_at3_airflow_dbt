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
        -- Use SCD Type 2 logic to get correct dimension values at point in time
        d.host_neighbourhood,
        -- Get LGA mapping to convert host_neighbourhood to LGA
        lga.lga_name as host_neighbourhood_lga
    from {{ ref('fact_listings') }} f
    left join {{ ref('dim_host') }} d
        on f.host_id = d.host_id
        and f.scraped_date >= d.dbt_valid_from::date
        and (f.scraped_date < d.dbt_valid_to::date or d.dbt_valid_to is null)
    left join {{ ref('silver_lga_mapping') }} lga
        on d.host_neighbourhood = lga.suburb_name_clean
),

monthly_metrics as (
    select
        host_neighbourhood_lga,
        scraped_year,
        scraped_month,
        -- Number of distinct hosts - per requirements
        count(distinct host_id) as distinct_hosts,
        -- Total estimated revenue (sum of all listings' revenue) - per requirements
        sum(estimated_revenue_30_days) as total_estimated_revenue,
        -- Estimated revenue per host (distinct) - per requirements: Total Revenue / Total Hosts
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
