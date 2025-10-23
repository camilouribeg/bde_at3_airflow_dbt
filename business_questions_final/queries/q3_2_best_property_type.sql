-- q3_2_best_property_type
-- Generated: 2025-10-21 11:48:13


        WITH top_5_neighbourhoods AS (
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
        