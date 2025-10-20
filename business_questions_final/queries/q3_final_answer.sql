-- q3_final_answer_corrected
-- Generated: 2025-10-21 10:38:53


        WITH top_5_neighbourhoods AS (
            -- Get top 5 neighbourhoods by revenue
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
        best_property_type AS (
            -- Find the property type with highest total stays
            SELECT 
                property_type,
                room_type,
                accommodates,
                SUM(total_stays) as total_stays,
                AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
                SUM(active_listings) as total_active_listings
            FROM public_gold.dm_property_type
            WHERE scraped_year >= 2020
            GROUP BY property_type, room_type, accommodates
            ORDER BY SUM(total_stays) DESC
            LIMIT 1
        )
        SELECT 
            'ANSWER' as analysis_type,
            bp.property_type as best_property_type,
            bp.room_type as best_room_type,
            bp.accommodates as best_accommodates,
            bp.total_stays as total_stays_achieved,
            bp.avg_revenue_per_active_listing as avg_revenue_per_active_listing,
            bp.total_active_listings as total_active_listings,
            'This property type achieves the highest number of stays across all neighbourhoods' as explanation
        FROM best_property_type bp;
        