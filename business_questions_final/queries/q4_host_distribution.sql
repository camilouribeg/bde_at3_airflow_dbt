-- q4_host_distribution
-- Generated: 2025-10-21 10:52:50


        WITH host_lga_analysis AS (
            -- Count listings per host per LGA over available 12 months (May 2020-April 2021)
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
            -- Summarize hosts with multiple listings
            SELECT 
                host_id,
                COUNT(DISTINCT lga_name) as lgas_count,
                SUM(listings_in_lga) as total_listings,
                SUM(total_stays_in_lga) as total_stays,
                AVG(avg_price_in_lga) as avg_price_across_lgas
            FROM host_lga_analysis
            GROUP BY host_id
            HAVING SUM(listings_in_lga) > 1  -- Only hosts with multiple listings
        )
        SELECT 
            hs.host_id,
            hs.lgas_count,
            hs.total_listings,
            hs.total_stays,
            hs.avg_price_across_lgas,
            CASE 
                WHEN hs.lgas_count = 1 THEN 'CONCENTRATED'
                ELSE 'DISTRIBUTED'
            END as distribution_type,
            -- Get LGA details for each host
            STRING_AGG(DISTINCT hla.lga_name, ', ') as lga_names,
            STRING_AGG(DISTINCT hla.lga_code, ', ') as lga_codes
        FROM host_summary hs
        JOIN host_lga_analysis hla ON hs.host_id = hla.host_id
        GROUP BY hs.host_id, hs.lgas_count, hs.total_listings, hs.total_stays, hs.avg_price_across_lgas
        ORDER BY hs.total_listings DESC, hs.lgas_count DESC;
        