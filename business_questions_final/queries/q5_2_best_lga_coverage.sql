-- q5_2_best_lga_coverage
-- Generated: 2025-10-21 11:48:22


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
            HAVING COUNT(*) >= 5
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
        