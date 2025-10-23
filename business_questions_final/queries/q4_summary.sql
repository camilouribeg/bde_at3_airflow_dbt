-- q4_summary
-- Generated: 2025-10-21 10:52:51


        WITH host_lga_analysis AS (
            SELECT 
                fl.host_id,
                ds.lga_name,
                lga.lga_code,
                COUNT(*) as listings_in_lga
            FROM public_gold.fact_listings fl
            JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE fl.scraped_date >= '2020-01-01'
            GROUP BY fl.host_id, ds.lga_name, lga.lga_code
        ),
        host_summary AS (
            SELECT 
                host_id,
                COUNT(DISTINCT lga_name) as lgas_count,
                SUM(listings_in_lga) as total_listings
            FROM host_lga_analysis
            GROUP BY host_id
            HAVING SUM(listings_in_lga) > 1
        )
        SELECT 
            'SUMMARY' as analysis_type,
            COUNT(*) as total_hosts_with_multiple_listings,
            COUNT(CASE WHEN lgas_count = 1 THEN 1 END) as concentrated_hosts,
            COUNT(CASE WHEN lgas_count > 1 THEN 1 END) as distributed_hosts,
            ROUND(COUNT(CASE WHEN lgas_count = 1 THEN 1 END)::numeric / COUNT(*) * 100, 2) as concentrated_percentage,
            ROUND(COUNT(CASE WHEN lgas_count > 1 THEN 1 END)::numeric / COUNT(*) * 100, 2) as distributed_percentage,
            AVG(total_listings) as avg_listings_per_host,
            AVG(lgas_count) as avg_lgas_per_host,
            MAX(lgas_count) as max_lgas_per_host
        FROM host_summary;
        