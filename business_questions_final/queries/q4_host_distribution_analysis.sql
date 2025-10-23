-- q4_host_distribution_analysis
-- Generated: 2025-10-21 11:48:13


        WITH host_lga_analysis AS (
            SELECT 
                fl.host_id,
                ds.lga_name,
                lga.lga_code,
                COUNT(*) as listings_in_lga,
                AVG(fl.price) as avg_price_in_lga,
                SUM(fl.number_of_stays) as total_stays_in_lga
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
                SUM(listings_in_lga) as total_listings,
                SUM(total_stays_in_lga) as total_stays,
                AVG(avg_price_in_lga) as avg_price_across_lgas,
                CASE 
                    WHEN COUNT(DISTINCT lga_name) = 1 THEN 'CONCENTRATED'
                    ELSE 'DISTRIBUTED'
                END as distribution_type
            FROM host_lga_analysis
            GROUP BY host_id
            HAVING SUM(listings_in_lga) > 1
        ),
        distribution_analysis AS (
            SELECT 
                COUNT(*) as total_hosts_with_multiple_listings,
                COUNT(CASE WHEN distribution_type = 'CONCENTRATED' THEN 1 END) as concentrated_hosts,
                COUNT(CASE WHEN distribution_type = 'DISTRIBUTED' THEN 1 END) as distributed_hosts,
                ROUND(COUNT(CASE WHEN distribution_type = 'CONCENTRATED' THEN 1 END)::numeric / COUNT(*) * 100, 1) as concentrated_percentage,
                ROUND(COUNT(CASE WHEN distribution_type = 'DISTRIBUTED' THEN 1 END)::numeric / COUNT(*) * 100, 1) as distributed_percentage
            FROM host_summary
        )
        SELECT 
            total_hosts_with_multiple_listings,
            concentrated_hosts,
            distributed_hosts,
            concentrated_percentage,
            distributed_percentage
        FROM distribution_analysis;
        