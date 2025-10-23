-- q2_age_revenue_correlation
-- Generated: 2025-10-21 11:48:12


        WITH lga_revenue_data AS (
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
        SELECT 
            lrd.lga_name,
            lrd.lga_code,
            lrd.avg_revenue_per_active_listing,
            lrd.months_with_data,
            lrd.total_active_listings,
            lrd.neighbourhoods_count,
            c1.male_population,
            c1.female_population,
            c1.total_population,
            c1.male_percentage,
            c1.female_percentage,
            c2.median_age_persons,
            c2.median_mortgage_repay_monthly,
            c2.median_tot_hhd_inc_weekly,
            c2.median_mortgage_repay_annual,
            c2.median_tot_hhd_inc_annual,
            c2.mortgage_to_income_ratio_pct
        FROM lga_revenue_data lrd
        LEFT JOIN public_silver.silver_census_g01 c1 ON 'LGA' || lrd.lga_code = c1.lga_code_2016
        LEFT JOIN public_silver.silver_census_g02 c2 ON 'LGA' || lrd.lga_code = c2.lga_code_2016
        WHERE c2.median_age_persons IS NOT NULL
        ORDER BY lrd.avg_revenue_per_active_listing DESC;
        