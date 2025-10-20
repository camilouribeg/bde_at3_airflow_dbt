-- q3_property_analysis_corrected
-- Generated: 2025-10-21 10:38:52


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
        property_analysis AS (
            -- Analyze property types across all data to find best performers
            SELECT 
                property_type,
                room_type,
                accommodates,
                SUM(total_stays) as total_stays,
                AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
                SUM(active_listings) as total_active_listings,
                COUNT(DISTINCT scraped_year || '-' || scraped_month) as months_with_data
            FROM public_gold.dm_property_type
            WHERE scraped_year >= 2020
            GROUP BY property_type, room_type, accommodates
        )
        SELECT 
            property_type,
            room_type,
            accommodates,
            total_stays,
            avg_revenue_per_active_listing,
            total_active_listings,
            months_with_data,
            ROW_NUMBER() OVER (ORDER BY total_stays DESC) as stays_rank,
            ROW_NUMBER() OVER (ORDER BY avg_revenue_per_active_listing DESC) as revenue_rank
        FROM property_analysis
        ORDER BY total_stays DESC, avg_revenue_per_active_listing DESC;
        