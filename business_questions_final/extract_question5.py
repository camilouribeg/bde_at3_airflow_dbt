#!/usr/bin/env python3
"""
Business Question 5 Extraction: Revenue vs Mortgage Coverage
Extract data to answer: For hosts with a single Airbnb listing does the estimated revenue
over the available 12 months (May 2020-April 2021) cover the annualised median mortgage
repayment in the corresponding LGA? Which LGA has the highest percentage of hosts that can cover it?
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


def extract_question5_data():
    """Extract data for Question 5: Revenue vs Mortgage Coverage"""
    print("🎯 BUSINESS QUESTION 5: Revenue vs Mortgage Coverage")
    print("=" * 80)

    conn = get_connection()
    if not conn:
        return

    try:
        # Query 1: Individual Host Analysis - Does revenue cover mortgage?
        print("\n📊 Step 1: Analyzing Individual Host Revenue vs Mortgage Coverage...")

        sql_q5_individual_analysis = """
        WITH single_listing_hosts AS (
            -- Identify hosts with only one listing over available 12 months (May 2020-April 2021)
            SELECT 
                host_id,
                COUNT(DISTINCT listing_id) as total_listings
            FROM public_gold.fact_listings
            WHERE scraped_date >= '2020-01-01'
            GROUP BY host_id
            HAVING COUNT(DISTINCT listing_id) = 1
        ),
        host_revenue_analysis AS (
            -- Calculate annual revenue for single listing hosts
            SELECT 
                slh.host_id,
                fl.listing_id,
                ds.lga_name,
                lga.lga_code,
                AVG(fl.price) as avg_daily_price,
                AVG(fl.number_of_stays) as avg_monthly_stays,
                AVG(fl.estimated_revenue_30_days) as avg_monthly_revenue,
                -- Estimate annual revenue (monthly * 12)
                AVG(fl.estimated_revenue_30_days) * 12 as estimated_annual_revenue,
                COUNT(DISTINCT fl.scraped_date) as days_with_data
            FROM single_listing_hosts slh
            JOIN public_gold.fact_listings fl ON slh.host_id = fl.host_id
            JOIN public_gold.dim_suburb ds ON SPLIT_PART(fl.neighbourhood_key, '|', 2) = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE fl.scraped_date >= '2020-01-01'
            GROUP BY slh.host_id, fl.listing_id, ds.lga_name, lga.lga_code
        ),
        lga_mortgage_data AS (
            -- Get mortgage data by LGA
            SELECT 
                lga_code_2016,
                median_mortgage_repay_annual
            FROM public_silver.silver_census_g02
            WHERE median_mortgage_repay_annual IS NOT NULL
        )
        SELECT 
            hra.host_id,
            hra.listing_id,
            hra.lga_name,
            hra.lga_code,
            hra.avg_daily_price,
            hra.avg_monthly_stays,
            hra.avg_monthly_revenue,
            hra.estimated_annual_revenue,
            hra.days_with_data,
            lmd.median_mortgage_repay_annual,
            -- Calculate coverage ratio
            CASE 
                WHEN lmd.median_mortgage_repay_annual > 0 
                THEN hra.estimated_annual_revenue / lmd.median_mortgage_repay_annual
                ELSE NULL 
            END as revenue_to_mortgage_ratio,
            -- Determine if revenue covers mortgage
            CASE 
                WHEN lmd.median_mortgage_repay_annual IS NOT NULL AND hra.estimated_annual_revenue >= lmd.median_mortgage_repay_annual 
                THEN 'COVERS'
                WHEN lmd.median_mortgage_repay_annual IS NOT NULL 
                THEN 'DOES_NOT_COVER'
                ELSE 'NO_MORTGAGE_DATA'
            END as mortgage_coverage_status
        FROM host_revenue_analysis hra
        LEFT JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
        ORDER BY hra.estimated_annual_revenue DESC;
        """

        # Save query
        save_query("q5_individual_analysis", sql_q5_individual_analysis)

        # Execute and save data
        individual_analysis_df = pd.read_sql(sql_q5_individual_analysis, conn)
        save_dataframe(
            individual_analysis_df,
            "q5_individual_analysis",
            "Individual host revenue vs mortgage coverage analysis",
        )

        # Show summary
        print(f"   📈 Found {len(individual_analysis_df)} single-listing hosts")

        # Analyze coverage patterns
        covers = individual_analysis_df[
            individual_analysis_df["mortgage_coverage_status"] == "COVERS"
        ]
        does_not_cover = individual_analysis_df[
            individual_analysis_df["mortgage_coverage_status"] == "DOES_NOT_COVER"
        ]
        no_data = individual_analysis_df[
            individual_analysis_df["mortgage_coverage_status"] == "NO_MORTGAGE_DATA"
        ]

        print(
            f"   ✅ Hosts that CAN cover mortgage: {len(covers)} ({len(covers)/len(individual_analysis_df)*100:.1f}%)"
        )
        print(
            f"   ❌ Hosts that CANNOT cover mortgage: {len(does_not_cover)} ({len(does_not_cover)/len(individual_analysis_df)*100:.1f}%)"
        )
        print(
            f"   ❓ Hosts with no mortgage data: {len(no_data)} ({len(no_data)/len(individual_analysis_df)*100:.1f}%)"
        )

        if len(individual_analysis_df) > 0:
            print(
                f"   📊 Average annual revenue: ${individual_analysis_df['estimated_annual_revenue'].mean():,.0f}"
            )
            print(
                f"   📊 Average mortgage repayment: ${individual_analysis_df['median_mortgage_repay_annual'].mean():,.0f}"
            )

            # Show examples
            print(f"\n✅ EXAMPLES OF HOSTS THAT CAN COVER MORTGAGE:")
            top_covers = covers.head(5)
            for idx, row in top_covers.iterrows():
                print(
                    f"   Host {row['host_id']}: ${row['estimated_annual_revenue']:,.0f} revenue vs ${row['median_mortgage_repay_annual']:,.0f} mortgage (ratio: {row['revenue_to_mortgage_ratio']:.2f})"
                )

        # Query 2: LGA Summary - Which LGA has highest percentage coverage?
        print("\n📊 Step 2: Analyzing LGA Coverage Percentages...")

        sql_q5_lga_summary = """
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
                AVG(hra.estimated_annual_revenue) as avg_annual_revenue,
                AVG(lmd.median_mortgage_repay_annual) as avg_mortgage_repayment,
                AVG(hra.estimated_annual_revenue / lmd.median_mortgage_repay_annual) as avg_coverage_ratio
            FROM host_revenue_analysis hra
            JOIN lga_mortgage_data lmd ON 'LGA' || hra.lga_code = lmd.lga_code_2016
            GROUP BY hra.lga_name, hra.lga_code
            HAVING COUNT(*) >= 5  -- Only LGAs with at least 5 hosts
        )
        SELECT 
            lga_name,
            lga_code,
            total_hosts,
            hosts_that_cover,
            hosts_that_dont_cover,
            ROUND(hosts_that_cover::numeric / total_hosts * 100, 2) as coverage_percentage,
            ROUND(avg_annual_revenue, 2) as avg_annual_revenue,
            ROUND(avg_mortgage_repayment, 2) as avg_mortgage_repayment,
            ROUND(avg_coverage_ratio, 2) as avg_coverage_ratio
        FROM lga_coverage_analysis
        ORDER BY coverage_percentage DESC, total_hosts DESC;
        """

        # Save query
        save_query("q5_lga_summary", sql_q5_lga_summary)

        # Execute and save data
        lga_summary_df = pd.read_sql(sql_q5_lga_summary, conn)
        save_dataframe(
            lga_summary_df,
            "q5_lga_summary",
            "LGA summary with coverage percentages",
        )

        # Show summary
        print(f"   📈 Found {len(lga_summary_df)} LGAs with sufficient data")

        if len(lga_summary_df) > 0:
            best_lga = lga_summary_df.iloc[0]
            print(f"   🏆 BEST LGA: {best_lga['lga_name']}")
            print(
                f"      📊 Coverage percentage: {best_lga['coverage_percentage']:.1f}%"
            )
            print(f"      👥 Total hosts: {best_lga['total_hosts']:.0f}")
            print(f"      ✅ Hosts that cover: {best_lga['hosts_that_cover']:.0f}")
            print(
                f"      💰 Avg annual revenue: ${best_lga['avg_annual_revenue']:,.0f}"
            )
            print(
                f"      🏠 Avg mortgage repayment: ${best_lga['avg_mortgage_repayment']:,.0f}"
            )

            # Show top 5 LGAs
            print(f"\n🏆 TOP 5 LGAs BY COVERAGE PERCENTAGE:")
            top_lgas = lga_summary_df.head(5)
            for idx, row in top_lgas.iterrows():
                print(
                    f"   {idx+1}. {row['lga_name']}: {row['coverage_percentage']:.1f}% ({row['hosts_that_cover']:.0f}/{row['total_hosts']:.0f} hosts)"
                )

        print(f"\n✅ Question 5 extraction completed!")
        print(f"   📁 Data files saved in: business_questions_final/data/")
        print(f"   📁 Query files saved in: business_questions_final/queries/")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_question5_data()
