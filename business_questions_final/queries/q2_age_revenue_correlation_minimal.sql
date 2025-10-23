-- q2_age_revenue_correlation_minimal
-- Generated: 2025-10-21 12:03:25


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
        