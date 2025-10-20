
    WITH lga_revenue AS (
        SELECT 
            dl.lga_code,
            dl.lga_name,
            AVG(dm.estimated_revenue_per_active_listing) as avg_revenue_per_listing
        FROM public_gold.dm_listing_neighbourhood dm
        JOIN public_gold.dim_lga dl ON dm.listing_neighbourhood = dl.lga_name
        WHERE dm.estimated_revenue_per_active_listing IS NOT NULL
        GROUP BY dl.lga_code, dl.lga_name
    ),
    ranked_lgas AS (
        SELECT 
            lga_code,
            lga_name,
            avg_revenue_per_listing,
            ROW_NUMBER() OVER (ORDER BY avg_revenue_per_listing DESC) as rank_desc,
            ROW_NUMBER() OVER (ORDER BY avg_revenue_per_listing ASC) as rank_asc
        FROM lga_revenue
    )
    SELECT 
        lga_code,
        lga_name,
        avg_revenue_per_listing,
        CASE 
            WHEN rank_desc <= 13 THEN 'Top 13'
            WHEN rank_asc <= 13 THEN 'Bottom 13'
            ELSE 'Middle'
        END as performance_category
    FROM ranked_lgas
    WHERE rank_desc <= 13 OR rank_asc <= 13
    ORDER BY avg_revenue_per_listing DESC;
    