#!/usr/bin/env python3
"""
Question 2 Minimal Extraction - Only Essential Columns
Extract only the columns needed to answer the correlation question
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


def extract_question2_minimal():
    """Extract Question 2 data with only essential columns"""
    print("🎯 QUESTION 2 MINIMAL EXTRACTION")
    print("=" * 50)

    conn = get_connection()
    if not conn:
        return

    try:
        print("\n📊 Question 2: Age vs Revenue Correlation (Minimal)...")

        sql_q2_minimal = """
        WITH lga_revenue_data AS (
            -- Calculate average revenue per active listing by LGA
            SELECT 
                lga.lga_name,
                lga.lga_code,
                AVG(dm.avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing
            FROM public_gold.dm_listing_neighbourhood dm
            JOIN public_gold.dim_suburb ds ON dm.listing_neighbourhood = ds.suburb_name
            JOIN public_gold.dim_lga lga ON UPPER(ds.lga_name) = UPPER(lga.lga_name)
            WHERE dm.scraped_year >= 2020
            GROUP BY lga.lga_name, lga.lga_code
            HAVING COUNT(DISTINCT dm.scraped_year || '-' || dm.scraped_month) >= 6
        )
        -- Join with demographic data from Census (age data only)
        SELECT 
            lrd.lga_name,
            lrd.avg_revenue_per_active_listing,
            c2.median_age_persons
        FROM lga_revenue_data lrd
        LEFT JOIN public_silver.silver_census_g02 c2 ON 'LGA' || lrd.lga_code = c2.lga_code_2016
        WHERE c2.median_age_persons IS NOT NULL  -- Only LGAs with age data
        ORDER BY lrd.avg_revenue_per_active_listing DESC;
        """

        save_query("q2_age_revenue_correlation_minimal", sql_q2_minimal)
        df = pd.read_sql(sql_q2_minimal, conn)
        save_dataframe(
            df,
            "q2_age_revenue_correlation_minimal",
            "Age vs revenue correlation data (minimal columns)",
        )

        # Calculate correlation
        correlation = df["median_age_persons"].corr(
            df["avg_revenue_per_active_listing"]
        )

        print(f"\n📈 CORRELATION ANALYSIS:")
        print(f"   📊 Correlation Coefficient: {correlation:.4f}")

        if abs(correlation) < 0.1:
            strength = "Very Weak"
        elif abs(correlation) < 0.3:
            strength = "Weak"
        elif abs(correlation) < 0.5:
            strength = "Moderate"
        elif abs(correlation) < 0.7:
            strength = "Strong"
        else:
            strength = "Very Strong"

        print(f"   📊 Correlation Strength: {strength}")
        print(
            f"   📊 Correlation Direction: {'Positive' if correlation > 0 else 'Negative'}"
        )
        print()

        print("✅ MINIMAL EXTRACTION COMPLETED!")
        print("   📁 Data file: q2_age_revenue_correlation_minimal.csv")
        print("   📁 Query file: q2_age_revenue_correlation_minimal.sql")
        print(
            "   📊 Columns: lga_name, avg_revenue_per_active_listing, median_age_persons"
        )
        print("   🎯 Perfect for screenshots and correlation analysis!")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_question2_minimal()
