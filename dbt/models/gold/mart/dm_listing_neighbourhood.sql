{{
    config(
        materialized='view',
        alias='dm_listing_neighbourhood'
    )
}}

with fact_with_dimensions as (
    select
        f.listing_id,
        f.scraped_date,
        f.scraped_year,
        f.scraped_month,
        f.price,
        f.has_availability,
        f.availability_30,
        f.number_of_stays,
        f.estimated_revenue_30_days,
        f.host_id,
        -- For now, let's use the Silver data directly to avoid SCD Type 2 complexity
        s.listing_neighbourhood_clean as listing_neighbourhood,
        s.host_neighbourhood_clean as host_neighbourhood
    from {{ ref('fact_listings') }} f
    left join {{ ref('silver_airbnb_listings') }} s
        on f.listing_id = s.listing_id
),

monthly_metrics as (
    select
        listing_neighbourhood,
        scraped_year,
        scraped_month,
        -- Total listings
        count(*) as total_listings,
        -- Active listings (has_availability = true)
        sum(case when has_availability then 1 else 0 end) as active_listings,
        -- Active listings rate (as percentage)
        round(
            (sum(case when has_availability then 1 else 0 end)::numeric / count(*)) * 100, 
            2
        ) as active_listings_rate,
        -- Price metrics for active listings
        min(case when has_availability then price end) as min_price_active,
        max(case when has_availability then price end) as max_price_active,
        round(
            (percentile_cont(0.5) within group (order by case when has_availability then price end))::numeric, 
            2
        ) as median_price_active,
        round(
            (avg(case when has_availability then price end))::numeric, 
            2
        ) as avg_price_active,
        -- Number of distinct hosts
        count(distinct host_id) as distinct_hosts,
        -- Total number of stays (only for active listings)
        sum(case when has_availability then number_of_stays else 0 end) as total_stays,
        -- Average estimated revenue per active listing
        round(
            (avg(case when has_availability then estimated_revenue_30_days end))::numeric, 
            2
        ) as avg_estimated_revenue_per_active_listing
    from fact_with_dimensions
    where listing_neighbourhood is not null
    group by listing_neighbourhood, scraped_year, scraped_month
),

monthly_with_lag as (
    select
        *,
        -- Calculate percentage change for active listings
        lag(active_listings) over (
            partition by listing_neighbourhood 
            order by scraped_year, scraped_month
        ) as prev_active_listings,
        -- Calculate percentage change for inactive listings
        lag(total_listings - active_listings) over (
            partition by listing_neighbourhood 
            order by scraped_year, scraped_month
        ) as prev_inactive_listings
    from monthly_metrics
)

select
    listing_neighbourhood,
    scraped_year,
    scraped_month,
    total_listings,
    active_listings,
    active_listings_rate,
    min_price_active,
    max_price_active,
    median_price_active,
    avg_price_active,
    distinct_hosts,
    total_stays,
    avg_estimated_revenue_per_active_listing,
    -- Percentage change for active listings
    case 
        when prev_active_listings > 0 then
            round(((active_listings - prev_active_listings)::numeric / prev_active_listings) * 100, 2)
        else null
    end as pct_change_active_listings,
    -- Percentage change for inactive listings
    case 
        when prev_inactive_listings > 0 then
            round(((total_listings - active_listings - prev_inactive_listings)::numeric / prev_inactive_listings) * 100, 2)
        else null
    end as pct_change_inactive_listings
from monthly_with_lag
order by listing_neighbourhood, scraped_year, scraped_month
