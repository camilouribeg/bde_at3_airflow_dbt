-- q5_individual_analysis
-- Generated: 2025-10-21 10:59:46


        WITH single_listing_hosts AS (
            -- Identify hosts with only one listing over available 12 months (May 2020-April 2021)
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
            JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
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
        