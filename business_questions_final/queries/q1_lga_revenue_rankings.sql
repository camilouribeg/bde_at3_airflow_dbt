
        WITH lga_revenue_ranking AS (
            -- Calculate average revenue per active listing by LGA over last 12 months
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
        