-- q3_1_top_neighbourhoods
-- Generated: 2025-10-21 11:48:12


        WITH neighbourhood_revenue_ranking AS (
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
        