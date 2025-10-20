#!/usr/bin/env python3
"""
Business Question 1: Demographic Differences Between Top 3 and Bottom 3 LGAs
Extract data for analysis of demographic differences between top 3 and lowest 3
performing LGAs based on estimated revenue per active listing.
"""

import psycopg2
import pandas as pd
from datetime import datetime
import os

# Database configuration
DB_CONFIG = {
    "host": "34.40.238.227",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "0t_:ETvs1.n|vMs,",
}


def get_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def save_query(query_name, sql_text):
    """Save SQL query to file"""
    os.makedirs("queries", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"queries/{query_name}_{timestamp}.sql"
    with open(filename, "w") as f:
        f.write(sql_text)
    print(f"✅ Query saved: {filename}")
    return filename


def save_dataframe(df, filename, description):
    """Save DataFrame to CSV"""
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"data/{filename}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)
    print(f"✅ Data saved: {csv_filename} ({len(df)} rows) - {description}")
    return csv_filename


def extract_question1_corrected():
    """Extract data for Business Question 1 - CORRECTED: Top 3 vs Bottom 3"""
    print("🎯 BUSINESS QUESTION 1: Demographic Differences Analysis (CORRECTED)")
    print("=" * 70)
    print("📊 Analyzing TOP 3 vs BOTTOM 3 LGAs (not top 13!)")
    print("=" * 70)

    conn = get_connection()
    if not conn:
        return

    try:
        # Query 1: Get Top 3 and Bottom 3 LGAs by Revenue per Active Listing
        print("\n📊 Step 1: Extracting Top 3 and Bottom 3 LGA Revenue Rankings...")

        sql_q1_lgas_corrected = """
        WITH lga_revenue_ranking AS (
            -- Calculate average revenue per active listing by LGA over available 12 months (May 2020-April 2021)
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
        )
        SELECT 
            lga_name,
            lga_code,
            avg_revenue_per_active_listing,
            months_with_data,
            total_active_listings,
            revenue_rank,
            CASE 
                WHEN revenue_rank <= 3 THEN 'TOP_3'
                WHEN revenue_rank > total_lgas - 3 THEN 'BOTTOM_3'
                ELSE 'MIDDLE'
            END as performance_group
        FROM ranked_lgas
        WHERE revenue_rank <= 3 OR revenue_rank > total_lgas - 3
        ORDER BY avg_revenue_per_active_listing DESC;
        """

        # Save query
        save_query("q1_lga_revenue_rankings", sql_q1_lgas_corrected)

        # Execute and save data
        lgas_df = pd.read_sql(sql_q1_lgas_corrected, conn)
        save_dataframe(
            lgas_df,
            "q1_lga_rankings",
            "LGA revenue rankings (top 3 + bottom 3)",
        )

        # Show summary
        top_lgas = lgas_df[lgas_df["performance_group"] == "TOP_3"]
        bottom_lgas = lgas_df[lgas_df["performance_group"] == "BOTTOM_3"]

        print(f"   📈 Found {len(top_lgas)} top-performing LGAs")
        print(f"   📉 Found {len(bottom_lgas)} bottom-performing LGAs")
        print(
            f"   💰 Revenue range: ${lgas_df['avg_revenue_per_active_listing'].min():,.0f} - ${lgas_df['avg_revenue_per_active_listing'].max():,.0f}"
        )

        # Show top 3 and bottom 3
        print(f"\n🏆 TOP 3 LGAs:")
        for idx, row in top_lgas.iterrows():
            print(
                f"   {row['revenue_rank']}. {row['lga_name']}: ${row['avg_revenue_per_active_listing']:,.0f}"
            )

        print(f"\n📉 BOTTOM 3 LGAs:")
        for idx, row in bottom_lgas.iterrows():
            print(
                f"   {row['revenue_rank']}. {row['lga_name']}: ${row['avg_revenue_per_active_listing']:,.0f}"
            )

        # Query 2: Get Demographic Data for Top 3 and Bottom 3 LGAs
        print("\n📊 Step 2: Extracting Demographic Data for Top 3 and Bottom 3...")

        sql_q1_demographics_corrected = """
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
        -- Join with demographic data from Census
        SELECT 
            tbl.lga_name,
            tbl.lga_code,
            tbl.avg_revenue_per_active_listing,
            tbl.revenue_rank,
            tbl.performance_group,
            -- Demographics from Census G01
            c1.male_population,
            c1.female_population,
            c1.total_population,
            c1.male_percentage,
            c1.female_percentage,
            -- Demographics from Census G02
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

        # Save query
        save_query("q1_demographic_analysis", sql_q1_demographics_corrected)

        # Execute and save data
        demographics_df = pd.read_sql(sql_q1_demographics_corrected, conn)
        save_dataframe(
            demographics_df,
            "q1_demographics",
            "Demographic data for top 3 and bottom 3 LGAs",
        )

        # Show summary
        with_census = demographics_df.dropna(subset=["median_age_persons"])
        print(
            f"   📈 LGAs with census data: {len(with_census)} out of {len(demographics_df)}"
        )

        if len(with_census) > 0:
            top_with_census = with_census[with_census["performance_group"] == "TOP_3"]
            bottom_with_census = with_census[
                with_census["performance_group"] == "BOTTOM_3"
            ]

            print(f"   🏆 Top 3 LGAs with census data: {len(top_with_census)}")
            print(f"   📉 Bottom 3 LGAs with census data: {len(bottom_with_census)}")

            # Show sample demographic data
            print(f"\n📊 Sample Demographic Data:")
            sample_cols = [
                "lga_name",
                "performance_group",
                "avg_revenue_per_active_listing",
                "median_age_persons",
                "male_percentage",
                "median_tot_hhd_inc_annual",
            ]
            print(with_census[sample_cols].head())

        print(f"\n✅ Business Question 1 CORRECTED extraction completed!")
        print(f"   📁 Files saved in: business_questions_final/")
        print(f"   📊 Ready for demographic analysis: TOP 3 vs BOTTOM 3!")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_question1_corrected()
