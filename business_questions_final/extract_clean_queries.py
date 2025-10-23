#!/usr/bin/env python3
"""
Clean Business Questions Extraction - Final Version
Extract data using the clean, optimized queries that directly answer each business question
"""

import pandas as pd
import psycopg2
from datetime import datetime
import os


def get_connection():
    """Create a connection to PostgreSQL database"""
    DB_CONFIG = {
        "host": "34.40.238.227",
        "port": 5432,
        "database": "postgres",
        "user": "postgres",
        "password": "0t_:ETvs1.n|vMs,",
    }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def save_query(query_name, query_sql):
    """Save SQL query to file"""
    os.makedirs("queries", exist_ok=True)
    with open(f"queries/{query_name}.sql", "w") as f:
        f.write(f"-- {query_name}\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(query_sql)

    print(f"   💾 Query saved: queries/{query_name}.sql")


def save_dataframe(df, filename_prefix, description):
    """Save DataFrame to CSV"""
    os.makedirs("data", exist_ok=True)
    csv_filename = f"data/{filename_prefix}.csv"
    df.to_csv(csv_filename, index=False)

    print(f"   💾 Data saved: {csv_filename}")
    print(f"   📊 Records: {len(df)}")
    print(f"   📋 Description: {description}")


def extract_clean_queries():
    """Extract data using clean queries that directly answer business questions"""
    print("🎯 CLEAN BUSINESS QUESTIONS EXTRACTION")
    print("=" * 80)

    conn = get_connection()
    if not conn:
        return

    try:
        # Query 1: Top/Bottom 3 LGAs with Demographics
        print("\n📊 Question 1: Top/Bottom 3 LGAs with Demographics...")

        sql_q1 = """
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
        SELECT 
            tbl.lga_name,
            tbl.lga_code,
            tbl.avg_revenue_per_active_listing,
            tbl.revenue_rank,
            tbl.performance_group,
            c1.male_population,
            c1.female_population,
            c1.total_population,
            c1.male_percentage,
            c1.female_percentage,
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
        """

        save_query("q1_top_bottom_lgas_demographics", sql_q1)
        df1 = pd.read_sql(sql_q1, conn)
        save_dataframe(
            df1,
            "q1_top_bottom_lgas_demographics",
            "Top 3 and Bottom 3 LGAs with demographic data",
        )

        # Query 2: Age vs Revenue Correlation
        print("\n📊 Question 2: Age vs Revenue Correlation...")

        sql_q2 = """
        WITH lga_revenue_data AS (
            SELECT 
                lga.lga_name,
                lga.lga_code,
                AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
                COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) as months_with_data,
                SUM(dm.active_listings) as total_active_listings,
                COUNT(DISTINCT dm.listing_neighbourhood) as neighbourhoods_count
            FROM public_gold.dm_listing_neighbourhood dm
            JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE dm.scraped_year >= 2020
            GROUP BY lga.lga_name, lga.lga_code
            HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
        )
        SELECT 
            lrd.lga_name,
            lrd.lga_code,
            lrd.avg_revenue_per_active_listing,
            lrd.months_with_data,
            lrd.total_active_listings,
            lrd.neighbourhoods_count,
            c1.male_population,
            c1.female_population,
            c1.total_population,
            c1.male_percentage,
            c1.female_percentage,
            c2.median_age_persons,
            c2.median_mortgage_repay_monthly,
            c2.median_tot_hhd_inc_weekly,
            c2.median_mortgage_repay_annual,
            c2.median_tot_hhd_inc_annual,
            c2.mortgage_to_income_ratio_pct
        FROM lga_revenue_data lrd
        LEFT JOIN public_silver.silver_census_g01 c1 ON 'LGA' || lrd.lga_code = c1.lga_code_2016
        LEFT JOIN public_silver.silver_census_g02 c2 ON 'LGA' || lrd.lga_code = c2.lga_code_2016
        WHERE c2.median_age_persons IS NOT NULL
        ORDER BY lrd.avg_revenue_per_active_listing DESC;
        """

        save_query("q2_age_revenue_correlation", sql_q2)
        df2 = pd.read_sql(sql_q2, conn)
        save_dataframe(
            df2, "q2_age_revenue_correlation", "LGA age vs revenue correlation data"
        )

        # Query 3.1: Top 5 Neighbourhoods
        print("\n📊 Question 3.1: Top 5 Neighbourhoods...")

        sql_q3_1 = """
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
        """

        save_query("q3_1_top_neighbourhoods", sql_q3_1)
        df3_1 = pd.read_sql(sql_q3_1, conn)
        save_dataframe(
            df3_1, "q3_1_top_neighbourhoods", "Top 5 neighbourhoods by revenue"
        )

        # Query 3.2: Best Property Type for Top 5 Neighbourhoods
        print("\n📊 Question 3.2: Best Property Type...")

        sql_q3_2 = """
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
        """

        save_query("q3_2_best_property_type", sql_q3_2)
        df3_2 = pd.read_sql(sql_q3_2, conn)
        save_dataframe(
            df3_2,
            "q3_2_best_property_type",
            "Best property type for top 5 neighbourhoods",
        )

        # Query 4: Host Distribution Analysis
        print("\n📊 Question 4: Host Distribution Analysis...")

        sql_q4 = """
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
        """

        save_query("q4_host_distribution_analysis", sql_q4)
        df4 = pd.read_sql(sql_q4, conn)
        save_dataframe(
            df4, "q4_host_distribution_analysis", "Host distribution analysis summary"
        )

        # Query 5.1: Overall Coverage Analysis
        print("\n📊 Question 5.1: Overall Coverage Analysis...")

        sql_q5_1 = """
        WITH single_listing_hosts AS (
            SELECT 
                host_id,
                COUNT(DISTINCT listing_id) as total_listings
            FROM public_gold.fact_listings
            WHERE scraped_date >= '2020-01-01'
            GROUP BY host_id
            HAVING COUNT(DISTINCT listing_id) = 1
        ),
        host_revenue_analysis AS (
            SELECT 
                slh.host_id,
                fl.listing_id,
                ds.lga_name,
                lga.lga_code,
                AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue
            FROM single_listing_hosts slh
            JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
            JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE fl.scraped_date >= '2020-01-01'
            GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
        ),
        lga_mortgage_data AS (
            SELECT 
                lga_code_2016,
                median_mortgage_repay_annual
            FROM public_silver.silver_census_g02
            WHERE median_mortgage_repay_annual IS NOT NULL
        ),
        coverage_analysis AS (
            SELECT 
                hra.host_id,
                hra.estimated_annual_revenue,
                lmd.median_mortgage_repay_annual,
                CASE 
                    WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual 
                    THEN 'COVERS'
                    ELSE 'DOES_NOT_COVER'
                END as mortgage_coverage_status
            FROM host_revenue_analysis hra
            JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
        )
        SELECT 
            COUNT(*) as total_single_listing_hosts,
            COUNT(CASE WHEN mortgage_coverage_status = 'COVERS' THEN 1 END) as hosts_that_cover,
            COUNT(CASE WHEN mortgage_coverage_status = 'DOES_NOT_COVER' THEN 1 END) as hosts_that_dont_cover,
            ROUND(COUNT(CASE WHEN mortgage_coverage_status = 'COVERS' THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_percentage,
            ROUND(COUNT(CASE WHEN mortgage_coverage_status = 'DOES_NOT_COVER' THEN 1 END)::numeric / COUNT(*) * 100, 1) as no_coverage_percentage
        FROM coverage_analysis;
        """

        save_query("q5_1_overall_coverage", sql_q5_1)
        df5_1 = pd.read_sql(sql_q5_1, conn)
        save_dataframe(
            df5_1, "q5_1_overall_coverage", "Overall mortgage coverage analysis"
        )

        # Query 5.2: Best LGA by Coverage
        print("\n📊 Question 5.2: Best LGA by Coverage...")

        sql_q5_2 = """
        WITH single_listing_hosts AS (
            SELECT 
                host_id,
                COUNT(DISTINCT listing_id) as total_listings
            FROM public_gold.fact_listings
            WHERE scraped_date >= '2020-01-01'
            GROUP BY host_id
            HAVING COUNT(DISTINCT listing_id) = 1
        ),
        host_revenue_analysis AS (
            SELECT 
                slh.host_id,
                fl.listing_id,
                ds.lga_name,
                lga.lga_code,
                AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue
            FROM single_listing_hosts slh
            JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
            JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE fl.scraped_date >= '2020-01-01'
            GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
        ),
        lga_mortgage_data AS (
            SELECT 
                lga_code_2016,
                median_mortgage_repay_annual
            FROM public_silver.silver_census_g02
            WHERE median_mortgage_repay_annual IS NOT NULL
        ),
        lga_coverage_analysis AS (
            SELECT 
                hra.lga_name,
                hra.lga_code,
                COUNT(*) as total_hosts,
                COUNT(CASE WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual THEN 1 END) as hosts_that_cover,
                COUNT(CASE WHEN hra.estimated_annual_revenue < lmd.median_mortgage_repay_annual THEN 1 END) as hosts_that_dont_cover,
                ROUND(COUNT(CASE WHEN hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual THEN 1 END)::numeric / COUNT(*) * 100, 1) as coverage_percentage
            FROM host_revenue_analysis hra
            JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
            GROUP BY hra.lga_name, hra.lga_code
            HAVING COUNT(*) >= 5
        )
        SELECT 
            lga_name,
            lga_code,
            total_hosts,
            hosts_that_cover,
            hosts_that_dont_cover,
            coverage_percentage
        FROM lga_coverage_analysis
        ORDER BY coverage_percentage DESC
        LIMIT 1;
        """

        save_query("q5_2_best_lga_coverage", sql_q5_2)
        df5_2 = pd.read_sql(sql_q5_2, conn)
        save_dataframe(
            df5_2, "q5_2_best_lga_coverage", "Best LGA by mortgage coverage percentage"
        )

        print(f"\n✅ All clean queries extracted successfully!")
        print(f"   📁 Data files saved in: business_questions_final/data/")
        print(f"   📁 Query files saved in: business_questions_final/queries/")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_clean_queries()
