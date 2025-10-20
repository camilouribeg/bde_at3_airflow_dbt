-- =====================================================
-- PART 4: BUSINESS QUESTIONS ANALYSIS
-- Assignment 3: Big Data Engineering
-- =====================================================
-- This file contains all SQL queries used for Part 4 business questions analysis
-- All queries are designed to run on PostgreSQL with the medallion architecture

-- =====================================================
-- BUSINESS QUESTION 1: Demographic Differences Analysis
-- =====================================================
-- Question: What are the demographic differences between the top 3 performing 
-- and lowest 3 performing LGAs based on estimated revenue per active listing 
-- over the available 12 months (May 2020-April 2021)?

-- Query 1.1: Get Top/Bottom 3 LGAs by Revenue per Active Listing
WITH lga_revenue_ranking AS (
    -- Calculate average revenue per active listing by LGA over available 12 months (May 2020-April 2021)
    SELECT 
        lga.lga_name,
        lga.lga_code,
        AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
        COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) as months_with_data,
        SUM(dm.active_listings) as total_active_listings
    FROM public_gold.dm_listing_neighbourhood dm
    JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE dm.scraped_year >= 2020
    GROUP BY lga.lga_name, lga.lga_code
    HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
),
ranked_lgas AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY avg_revenue_per_active_listing DESC) as revenue_rank,
        COUNT(*) OVER () as total_lgas
    FROM lga_revenue_ranking
)
SELECT 
    lga_name,
    lga_code,
    avg_revenue_per_active_listing,
    months_with_data,
    total_active_listings,
    revenue_rank,
    CASE 
        WHEN revenue_rank <= 3 THEN 'TOP_3'
        WHEN revenue_rank > total_lgas - 3 THEN 'BOTTOM_3'
        ELSE 'MIDDLE'
    END as performance_group
FROM ranked_lgas
WHERE revenue_rank <= 3 OR revenue_rank > total_lgas - 3
ORDER BY avg_revenue_per_active_listing DESC;

-- Query 1.2: Get Demographic Data for Top/Bottom LGAs
WITH lga_revenue_ranking AS (
    SELECT 
        lga.lga_name,
        lga.lga_code,
        AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
        COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) as months_with_data,
        SUM(dm.active_listings) as total_active_listings
    FROM public_gold.dm_listing_neighbourhood dm
    JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE dm.scraped_year >= 2020
    GROUP BY lga.lga_name, lga.lga_code
    HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
),
ranked_lgas AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY avg_revenue_per_active_listing DESC) as revenue_rank,
        COUNT(*) OVER () as total_lgas
    FROM lga_revenue_ranking
),
top_bottom_lgas AS (
    SELECT 
        lga_name,
        lga_code,
        avg_revenue_per_active_listing,
        revenue_rank,
        CASE 
            WHEN revenue_rank <= 3 THEN 'TOP_3'
            WHEN revenue_rank > total_lgas - 3 THEN 'BOTTOM_3'
        END as performance_group
    FROM ranked_lgas
    WHERE revenue_rank <= 3 OR revenue_rank > total_lgas - 3
)
-- Join with demographic data from Census
SELECT 
    tbl.lga_name,
    tbl.lga_code,
    tbl.avg_revenue_per_active_listing,
    tbl.revenue_rank,
    tbl.performance_group,
    -- Demographics from Census G01
    c1.male_population,
    c1.female_population,
    c1.total_population,
    c1.male_percentage,
    c1.female_percentage,
    -- Demographics from Census G02
    c2.median_age_persons,
    c2.median_mortgage_repay_monthly,
    c2.median_tot_hhd_inc_weekly,
    c2.median_mortgage_repay_annual,
    c2.median_tot_hhd_inc_annual,
    c2.mortgage_to_income_ratio_pct
FROM top_bottom_lgas tbl
LEFT JOIN public_gold.dim_lga dl ON tbl.lga_name = dl.lga_name
LEFT JOIN public_silver.silver_census_g01 c1 ON 'LGA' || tbl.lga_code = c1.lga_code_2016
LEFT JOIN public_silver.silver_census_g02 c2 ON 'LGA' || tbl.lga_code = c2.lga_code_2016
ORDER BY tbl.avg_revenue_per_active_listing DESC;

-- =====================================================
-- BUSINESS QUESTION 2: Age vs Revenue Correlation
-- =====================================================
-- Question: Is there a correlation between the median age of a neighbourhood 
-- (from Census data) and the revenue generated per active listing in that neighbourhood?

WITH lga_revenue_data AS (
    -- Calculate average revenue per active listing by LGA
    SELECT 
        lga.lga_name,
        lga.lga_code,
        AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
        COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) as months_with_data,
        SUM(dm.active_listings) as total_active_listings,
        COUNT(DISTINCT dm.listing_neighbourhood) as neighbourhoods_count
    FROM public_gold.dm_listing_neighbourhood dm
    JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE dm.scraped_year >= 2020
    GROUP BY lga.lga_name, lga.lga_code
    HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
)
-- Join with demographic data from Census
SELECT 
    lrd.lga_name,
    lrd.lga_code,
    lrd.avg_revenue_per_active_listing,
    lrd.months_with_data,
    lrd.total_active_listings,
    lrd.neighbourhoods_count,
    -- Demographics from Census G01
    c1.male_population,
    c1.female_population,
    c1.total_population,
    c1.male_percentage,
    c1.female_percentage,
    -- Demographics from Census G02 (age data)
    c2.median_age_persons,
    c2.median_mortgage_repay_monthly,
    c2.median_tot_hhd_inc_weekly,
    c2.median_mortgage_repay_annual,
    c2.median_tot_hhd_inc_annual,
    c2.mortgage_to_income_ratio_pct
FROM lga_revenue_data lrd
LEFT JOIN public_silver.silver_census_g01 c1 ON 'LGA' || lrd.lga_code = c1.lga_code_2016
LEFT JOIN public_silver.silver_census_g02 c2 ON 'LGA' || lrd.lga_code = c2.lga_code_2016
WHERE c2.median_age_persons IS NOT NULL  -- Only LGAs with age data
ORDER BY lrd.avg_revenue_per_active_listing DESC;

-- =====================================================
-- BUSINESS QUESTION 3: Best Listing Type for Top Neighbourhoods
-- =====================================================
-- Question: What will be the best type of listing (property type, room type and accommodates) 
-- for the top 5 "listing_neighbourhood" (in terms of estimated revenue per active listing) 
-- to have the highest number of stays?

-- Query 3.1: Get Top 5 Neighbourhoods by Revenue per Active Listing
WITH neighbourhood_revenue_ranking AS (
    -- Calculate average revenue per active listing by neighbourhood
    SELECT 
        listing_neighbourhood,
        AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
        COUNT(DISTINCT scraped_year || '-' || scraped_month) as months_with_data,
        SUM(active_listings) as total_active_listings,
        SUM(total_stays) as total_stays
    FROM public_gold.dm_listing_neighbourhood
    WHERE scraped_year >= 2020
    GROUP BY listing_neighbourhood
    HAVING COUNT(DISTINCT scraped_year || '-' || scraped_month) >= 6
),
ranked_neighbourhoods AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY avg_revenue_per_active_listing DESC) as revenue_rank
    FROM neighbourhood_revenue_ranking
)
SELECT 
    listing_neighbourhood,
    avg_revenue_per_active_listing,
    months_with_data,
    total_active_listings,
    total_stays,
    revenue_rank
FROM ranked_neighbourhoods
WHERE revenue_rank <= 5
ORDER BY avg_revenue_per_active_listing DESC;

-- Query 3.2: Analyze Property Types by Total Stays
-- Analyze property types by total stays to find best types
SELECT 
    property_type,
    room_type,
    accommodates,
    AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_listing,
    SUM(total_stays) as total_stays_for_property_type,
    COUNT(DISTINCT scraped_year || '-' || scraped_month) as months_with_data,
    SUM(active_listings) as total_active_listings,
    -- Calculate stays per listing
    CASE 
        WHEN SUM(active_listings) > 0 
        THEN SUM(total_stays)::numeric / SUM(active_listings)
        ELSE 0 
    END as avg_stays_per_listing,
    -- Calculate revenue per stay
    CASE 
        WHEN SUM(total_stays) > 0 
        THEN AVG(avg_estimated_revenue_per_active_listing)::numeric / (SUM(total_stays)::numeric / SUM(active_listings))
        ELSE 0 
    END as revenue_per_stay
FROM public_gold.dm_property_type
WHERE scraped_year >= 2020
GROUP BY property_type, room_type, accommodates
HAVING COUNT(DISTINCT scraped_year || '-' || scraped_month) >= 6
ORDER BY total_stays_for_property_type DESC;

-- =====================================================
-- BUSINESS QUESTION 4: Host Distribution Across LGAs
-- =====================================================
-- Question: For hosts with multiple listings in Vic are their properties concentrated 
-- within the same LGA, or are they distributed across different LGAs?

WITH host_lga_analysis AS (
    -- Count listings per host per LGA
    SELECT 
        fl.host_id,
        ds.lga_name,
        lga.lga_code,
        COUNT(*) as listings_in_lga,
        AVG(fl.price) as avg_price_in_lga,
        SUM(fl.number_of_stays) as total_stays_in_lga
    FROM public_gold.fact_listings fl
    JOIN public_gold.dim_suburb ds ON fl.neighbourhood_key = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE fl.scraped_date >= '2020-01-01'
    GROUP BY fl.host_id, ds.lga_name, lga.lga_code
),
host_summary AS (
    -- Summarize hosts with multiple listings
    SELECT 
        host_id,
        COUNT(DISTINCT lga_name) as lgas_count,
        SUM(listings_in_lga) as total_listings,
        SUM(total_stays_in_lga) as total_stays,
        AVG(avg_price_in_lga) as avg_price_across_lgas
    FROM host_lga_analysis
    GROUP BY host_id
    HAVING SUM(listings_in_lga) > 1  -- Only hosts with multiple listings
)
SELECT 
    hs.host_id,
    hs.lgas_count,
    hs.total_listings,
    hs.total_stays,
    hs.avg_price_across_lgas,
    CASE 
        WHEN hs.lgas_count = 1 THEN 'CONCENTRATED'
        ELSE 'DISTRIBUTED'
    END as distribution_type,
    -- Get LGA details for each host
    STRING_AGG(DISTINCT hla.lga_name, ', ') as lga_names,
    STRING_AGG(DISTINCT hla.lga_code, ', ') as lga_codes
FROM host_summary hs
JOIN host_lga_analysis hla ON hs.host_id = hla.host_id
GROUP BY hs.host_id, hs.lgas_count, hs.total_listings, hs.total_stays, hs.avg_price_across_lgas
ORDER BY hs.total_listings DESC, hs.lgas_count DESC;

-- =====================================================
-- BUSINESS QUESTION 5: Revenue vs Mortgage Coverage
-- =====================================================
-- Question: For hosts with a single Airbnb listing does the estimated revenue 
-- over the available 12 months (May 2020-April 2021) cover the annualised median mortgage repayment in the 
-- corresponding LGA? Which LGA has the highest percentage of hosts that can cover it?

WITH single_listing_hosts AS (
    -- Identify hosts with only one listing
    SELECT 
        host_id,
        COUNT(DISTINCT listing_id) as total_listings
    FROM public_gold.fact_listings
    WHERE scraped_date >= '2020-01-01'
    GROUP BY host_id
    HAVING COUNT(DISTINCT listing_id) = 1
),
host_revenue_analysis AS (
    -- Calculate annual revenue for single listing hosts
    SELECT 
        slh.host_id,
        fl.listing_id,
        ds.lga_name,
        lga.lga_code,
        AVG(fl.price) as avg_daily_price,
        AVG(fl.number_of_stays) as avg_monthly_stays,
        AVG(fl.estimated_revenue_30_days) as avg_monthly_revenue,
        -- Estimate annual revenue (monthly * 12)
        AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue,
        COUNT(DISTINCT fl.scraped_date) as days_with_data
    FROM single_listing_hosts slh
    JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
    JOIN public_gold.dim_suburb ds ON fl.neighbourhood_key = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE fl.scraped_date >= '2020-01-01'
    GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
),
lga_mortgage_data AS (
    -- Get mortgage data by LGA
    SELECT 
        lga_code_2016,
        median_mortgage_repay_annual
    FROM public_silver.silver_census_g02
    WHERE median_mortgage_repay_annual IS NOT NULL
)
SELECT 
    hra.host_id,
    hra.listing_id,
    hra.lga_name,
    hra.lga_code,
    hra.avg_daily_price,
    hra.avg_monthly_stays,
    hra.avg_monthly_revenue,
    hra.estimated_annual_revenue,
    hra.days_with_data,
    lmd.median_mortgage_repay_annual,
    -- Calculate coverage ratio
    CASE 
        WHEN lmd.median_mortgage_repay_annual > 0 
        THEN hra.estimated_annual_revenue / lmd.median_mortgage_repay_annual
        ELSE NULL 
    END as revenue_to_mortgage_ratio,
    -- Determine if revenue covers mortgage
    CASE 
        WHEN lmd.median_mortgage_repay_annual IS NOT NULL AND hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual 
        THEN 'COVERS'
        WHEN lmd.median_mortgage_repay_annual IS NOT NULL 
        THEN 'DOES_NOT_COVER'
        ELSE 'NO_MORTGAGE_DATA'
    END as mortgage_coverage_status
FROM host_revenue_analysis hra
LEFT JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
ORDER BY hra.estimated_annual_revenue DESC;

-- =====================================================
-- END OF PART 4 SQL QUERIES
-- =====================================================
