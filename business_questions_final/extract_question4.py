#!/usr/bin/env python3
"""
Business Question 4 Extraction: Host Distribution Across LGAs
Extract data to answer: For hosts with multiple listings in Vic are their properties
concentrated within the same LGA, or are they distributed across different LGAs?
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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(f"queries/{query_name}_{timestamp}.sql", "w") as f:
        f.write(f"-- {query_name}\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(query_sql)

    print(f"   💾 Query saved: queries/{query_name}_{timestamp}.sql")


def save_dataframe(df, filename_prefix, description):
    """Save DataFrame to CSV"""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_filename = f"data/{filename_prefix}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)

    print(f"   💾 Data saved: {csv_filename}")
    print(f"   📊 Records: {len(df)}")
    print(f"   📋 Description: {description}")


def extract_question4_data():
    """Extract data for Question 4: Host distribution across LGAs"""
    print("🎯 BUSINESS QUESTION 4: Host Distribution Across LGAs")
    print("=" * 80)

    conn = get_connection()
    if not conn:
        return

    try:
        # Query: Host Distribution Analysis
        print("\n📊 Extracting Host Distribution Analysis...")

        sql_q4_host_distribution = """
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
        """

        # Save query
        save_query("q4_host_distribution", sql_q4_host_distribution)

        # Execute and save data
        host_distribution_df = pd.read_sql(sql_q4_host_distribution, conn)
        save_dataframe(
            host_distribution_df,
            "q4_host_distribution",
            "Host distribution analysis across LGAs",
        )

        # Show summary
        print(f"   📈 Found {len(host_distribution_df)} hosts with multiple listings")

        # Analyze distribution patterns
        concentrated = host_distribution_df[
            host_distribution_df["distribution_type"] == "CONCENTRATED"
        ]
        distributed = host_distribution_df[
            host_distribution_df["distribution_type"] == "DISTRIBUTED"
        ]

        print(
            f"   🏠 Concentrated hosts (same LGA): {len(concentrated)} ({len(concentrated)/len(host_distribution_df)*100:.1f}%)"
        )
        print(
            f"   🌐 Distributed hosts (multiple LGAs): {len(distributed)} ({len(distributed)/len(host_distribution_df)*100:.1f}%)"
        )

        if len(host_distribution_df) > 0:
            print(
                f"   📊 Average listings per host: {host_distribution_df['total_listings'].mean():.1f}"
            )
            print(
                f"   📊 Average LGAs per host: {host_distribution_df['lgas_count'].mean():.1f}"
            )

            # Show top distributed hosts
            print(f"\n🌐 TOP 5 MOST DISTRIBUTED HOSTS:")
            top_distributed = distributed.head(5)
            for idx, row in top_distributed.iterrows():
                print(
                    f"   Host {row['host_id']}: {row['lgas_count']} LGAs, {row['total_listings']} listings"
                )
                print(f"      LGAs: {row['lga_names']}")

            # Show top concentrated hosts
            print(f"\n🏠 TOP 5 MOST CONCENTRATED HOSTS:")
            top_concentrated = concentrated.head(5)
            for idx, row in top_concentrated.iterrows():
                print(
                    f"   Host {row['host_id']}: {row['total_listings']} listings in {row['lga_names']}"
                )

        # Query 2: Summary Statistics
        print("\n📊 Extracting Summary Statistics...")

        sql_q4_summary = """
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
        """

        # Save query
        save_query("q4_summary", sql_q4_summary)

        # Execute and save data
        summary_df = pd.read_sql(sql_q4_summary, conn)
        save_dataframe(
            summary_df,
            "q4_summary",
            "Summary statistics for host distribution analysis",
        )

        # Show summary results
        if not summary_df.empty:
            summary = summary_df.iloc[0]
            print(f"\n📊 SUMMARY STATISTICS:")
            print(
                f"   📈 Total hosts with multiple listings: {summary['total_hosts_with_multiple_listings']:,.0f}"
            )
            print(
                f"   🏠 Concentrated hosts: {summary['concentrated_hosts']:,.0f} ({summary['concentrated_percentage']:.1f}%)"
            )
            print(
                f"   🌐 Distributed hosts: {summary['distributed_hosts']:,.0f} ({summary['distributed_percentage']:.1f}%)"
            )
            print(
                f"   📊 Average listings per host: {summary['avg_listings_per_host']:.1f}"
            )
            print(f"   📊 Average LGAs per host: {summary['avg_lgas_per_host']:.1f}")
            print(f"   📊 Maximum LGAs per host: {summary['max_lgas_per_host']:.0f}")

        print(f"\n✅ Question 4 extraction completed!")
        print(f"   📁 Data files saved in: business_questions_final/data/")
        print(f"   📁 Query files saved in: business_questions_final/queries/")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_question4_data()
