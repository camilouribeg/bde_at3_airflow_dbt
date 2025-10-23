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

-- Query 2: Age vs Revenue Correlation (Minimal)
-- Answers: Is there a correlation between the median age of a neighbourhood 
-- (from Census data) and the revenue generated per active listing in that neighbourhood?
WITH lga_revenue_data AS (
    -- Calculate average revenue per active listing by LGA
    SELECT 
        lga.lga_name,
        lga.lga_code,
        AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing
    FROM public_gold.dm_listing_neighbourhood dm
    JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE dm.scraped_year >= 2020
    GROUP BY lga.lga_name, lga.lga_code
    HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
)
-- Join with demographic data from Census (age data only)
SELECT 
    lrd.lga_name,
    lrd.avg_revenue_per_active_listing,
    c2.median_age_persons
FROM lga_revenue_data lrd
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

-- Query 3.2: BEST Property Type for Top 5 Neighbourhoods (Minimal)
-- Find the best property type specifically for the top 5 neighbourhoods from Query 3.1
-- This query gives you exactly what the question asks for - no extra information
WITH top_5_neighbourhoods AS (
    -- Get the top 5 neighbourhoods from Query 3.1
    SELECT 
        listing_neighbourhood,
        AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing
    FROM public_gold.dm_listing_neighbourhood
    WHERE scraped_year >= 2020
    GROUP BY listing_neighbourhood
    HAVING COUNT(DISTINCT scraped_year || '-' || scraped_month) >= 6
    ORDER BY AVG(avg_estimated_revenue_per_active_listing) DESC
    LIMIT 5
),
property_analysis AS (
    -- Analyze property types specifically for the top 5 neighbourhoods
    SELECT 
        dp.property_type,
        dp.room_type,
        dp.accommodates,
        SUM(fl.number_of_stays) as total_stays
    FROM public_gold.fact_listings fl
    JOIN public_gold.dim_property dp ON fl.property_key = dp.property_key
    JOIN public_gold.dim_neighbourhood dn ON fl.neighbourhood_key = dn.neighbourhood_key
    JOIN top_5_neighbourhoods t5n ON dn.listing_neighbourhood = t5n.listing_neighbourhood
    WHERE fl.scraped_date >= '2020-01-01'
    GROUP BY dp.property_type, dp.room_type, dp.accommodates
)
SELECT 
    property_type,
    room_type,
    accommodates,
    total_stays
FROM property_analysis
ORDER BY total_stays DESC
LIMIT 1;

-- =====================================================
-- BUSINESS QUESTION 4: Host Distribution Across LGAs
-- =====================================================
-- Question: For hosts with multiple listings in Vic are their properties concentrated 
-- within the same LGA, or are they distributed across different LGAs?

-- Query 4: Host Distribution Analysis - Final Clean Version
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
    JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
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
        AVG(avg_price_in_lga) as avg_price_across_lgas,
        CASE 
            WHEN COUNT(DISTINCT lga_name) = 1 THEN 'CONCENTRATED'
            ELSE 'DISTRIBUTED'
        END as distribution_type
    FROM host_lga_analysis
    GROUP BY host_id
    HAVING SUM(listings_in_lga) > 1  -- Only hosts with multiple listings
),
distribution_analysis AS (
    -- Calculate summary statistics
    SELECT 
        COUNT(*) as total_hosts_with_multiple_listings,
        COUNT(CASE WHEN distribution_type = 'CONCENTRATED' THEN 1 END) as concentrated_hosts,
        COUNT(CASE WHEN distribution_type = 'DISTRIBUTED' THEN 1 END) as distributed_hosts,
        ROUND(COUNT(CASE WHEN distribution_type = 'CONCENTRATED' THEN 1 END)::numeric / COUNT(*) * 100, 1) as concentrated_percentage,
        ROUND(COUNT(CASE WHEN distribution_type = 'DISTRIBUTED' THEN 1 END)::numeric / COUNT(*) * 100, 1) as distributed_percentage
    FROM host_summary
)
SELECT 
    total_hosts_with_multiple_listings,
    concentrated_hosts,
    distributed_hosts,
    concentrated_percentage,
    distributed_percentage
FROM distribution_analysis;

-- =====================================================
-- BUSINESS QUESTION 5: Revenue vs Mortgage Coverage
-- =====================================================
-- Question: For hosts with a single Airbnb listing does the estimated revenue 
-- over the available 12 months (May 2020-April 2021) cover the annualised median mortgage repayment in the 
-- corresponding LGA? Which LGA has the highest percentage of hosts that can cover it?

-- Query 5.1: Overall Coverage Analysis
-- Answers: What percentage of single-listing hosts can cover their mortgage?
WITH single_listing_hosts AS (
    SELECT 
        host_id,
        COUNT(DISTINCT listing_id) as total_listings
    FROM public_gold.fact_listings
    WHERE scraped_date >= '2020-01-01'
    GROUP BY host_id
    HAVING COUNT(DISTINCT listing_id) = 1
),
host_revenue_analysis AS (
    SELECT 
        slh.host_id,
        fl.listing_id,
        ds.lga_name,
        lga.lga_code,
        AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue
    FROM single_listing_hosts slh
    JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
    JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE fl.scraped_date >= '2020-01-01'
    GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
),
lga_mortgage_data AS (
    SELECT 
        lga_code_2016,
        median_mortgage_repay_annual
    FROM public_silver.silver_census_g02
    WHERE median_mortgage_repay_annual IS NOT NULL
),
coverage_analysis AS (
    SELECT 
        hra.host_id,
        hra.estimated_annual_revenue,
        lmd.median_mortgage_repay_annual,
        CASE 
            WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual 
            THEN 'COVERS'
            ELSE 'DOES_NOT_COVER'
        END as mortgage_coverage_status
    FROM host_revenue_analysis hra
    JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
)
SELECT 
    COUNT(*) as total_single_listing_hosts,
    COUNT(CASE WHEN mortgage_coverage_status = 'COVERS' THEN 1 END) as hosts_that_cover,
    COUNT(CASE WHEN mortgage_coverage_status = 'DOES_NOT_COVER' THEN 1 END) as hosts_that_dont_cover,
    ROUND(COUNT(CASE WHEN mortgage_coverage_status = 'COVERS' THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_percentage,
    ROUND(COUNT(CASE WHEN mortgage_coverage_status = 'DOES_NOT_COVER' THEN 1 END)::numeric / COUNT(*) * 100, 1) as no_coverage_percentage
FROM coverage_analysis;

-- Query 5.2: Best LGA by Coverage Percentage
-- Answers: Which LGA has the highest percentage of hosts that can cover it?
WITH single_listing_hosts AS (
    SELECT 
        host_id,
        COUNT(DISTINCT listing_id) as total_listings
    FROM public_gold.fact_listings
    WHERE scraped_date >= '2020-01-01'
    GROUP BY host_id
    HAVING COUNT(DISTINCT listing_id) = 1
),
host_revenue_analysis AS (
    SELECT 
        slh.host_id,
        fl.listing_id,
        ds.lga_name,
        lga.lga_code,
        AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue
    FROM single_listing_hosts slh
    JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
    JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
    JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
    WHERE fl.scraped_date >= '2020-01-01'
    GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
),
lga_mortgage_data AS (
    SELECT 
        lga_code_2016,
        median_mortgage_repay_annual
    FROM public_silver.silver_census_g02
    WHERE median_mortgage_repay_annual IS NOT NULL
),
lga_coverage_analysis AS (
    SELECT 
        hra.lga_name,
        hra.lga_code,
        COUNT(*) as total_hosts,
        COUNT(CASE WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual THEN 1 END) as hosts_that_cover,
        COUNT(CASE WHEN hra.estimated_annual_revenue < lmd.median_mortgage_repay_annual THEN 1 END) as hosts_that_dont_cover,
        ROUND(COUNT(CASE WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_percentage
    FROM host_revenue_analysis hra
    JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
    GROUP BY hra.lga_name, hra.lga_code
    HAVING COUNT(*) >= 5  -- Only LGAs with at least 5 hosts
)
SELECT 
    lga_name,
    lga_code,
    total_hosts,
    hosts_that_cover,
    hosts_that_dont_cover,
    coverage_percentage
FROM lga_coverage_analysis
ORDER BY coverage_percentage DESC
LIMIT 1;

-- =====================================================
-- END OF PART 4 SQL QUERIES
-- =====================================================
