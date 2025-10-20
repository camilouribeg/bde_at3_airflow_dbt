
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
        