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
        f.host_is_superhost,
        f.review_scores_rating,
        -- Use SCD Type 2 logic to get correct dimension values at point in time
        d.listing_neighbourhood,
        d.host_neighbourhood
    from {{ ref('fact_listings') }} f
    left join {{ ref('dim_neighbourhood') }} d
        on f.neighbourhood_key = d.neighbourhood_key
        and f.scraped_date >= d.dbt_valid_from::date
        and (f.scraped_date < d.dbt_valid_to::date or d.dbt_valid_to is null)
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
        -- Active listings rate (as percentage) - per requirements: (active/total) * 100
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
        -- Superhost rate - per requirements: (superhosts/total hosts) * 100
        round(
            (count(distinct case when host_is_superhost then host_id end)::numeric / count(distinct host_id)) * 100, 
            2
        ) as superhost_rate,
        -- Average of review_scores_rating for active listings
        round(
            (avg(case when has_availability then review_scores_rating end))::numeric, 
            2
        ) as avg_review_scores_rating_active,
        -- Total Number of stays (only for active listings)
        sum(case when has_availability then number_of_stays else 0 end) as total_stays,
        -- Average Estimated revenue per active listings
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
        -- Calculate percentage change for active listings - per requirements: ((final-original)/original) * 100
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
    superhost_rate,
    avg_review_scores_rating_active,
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
