#!/usr/bin/env python3
"""
Mart Tables Diagnosis Script

This script helps diagnose why mart tables are returning null rows.
It checks the data flow from bronze -> silver -> gold -> mart tables.
"""

import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import logging

# Database connection parameters
# TODO: Update these with your actual database details
DB_CONFIG = {
    "host": "34.40.238.227",  # Replace with your PostgreSQL public IP
    "port": 5432,
    "database": "postgres",  # or your database name
    "user": "postgres",  # or your username
    "password": "0t_:ETvs1.n|vMs,",  # Replace with your password
}


def get_connection():
    """Create a connection to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def get_sqlalchemy_engine():
    """Create SQLAlchemy engine for pandas operations"""
    try:
        connection_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None


def check_bronze_data():
    """Check bronze table data"""
    print("=" * 60)
    print("CHECKING BRONZE TABLE DATA")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        # Check bronze_airbnb_listings
        df = pd.read_sql(
            "SELECT COUNT(*) as count FROM bronze.bronze_airbnb_listings", engine
        )
        count = df["count"].iloc[0]
        print(f"bronze_airbnb_listings: {count} rows")

        if count > 0:
            # Check sample data
            sample_df = pd.read_sql(
                """
                SELECT listing_id, host_id, property_type, room_type, 
                       listing_neighbourhood, host_neighbourhood, scraped_date
                FROM bronze.bronze_airbnb_listings 
                LIMIT 3
            """,
                engine,
            )
            print("Sample bronze data:")
            print(sample_df.to_string())

        return count > 0

    except Exception as e:
        print(f"❌ Error checking bronze data: {e}")
        return False


def check_silver_data():
    """Check silver table data"""
    print("\n" + "=" * 60)
    print("CHECKING SILVER TABLE DATA")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        # Check silver_airbnb_listings
        df = pd.read_sql(
            "SELECT COUNT(*) as count FROM silver.silver_airbnb_listings", engine
        )
        count = df["count"].iloc[0]
        print(f"silver_airbnb_listings: {count} rows")

        if count > 0:
            # Check sample data
            sample_df = pd.read_sql(
                """
                SELECT listing_id, host_id, property_type_clean, room_type_clean, 
                       listing_neighbourhood_clean, host_neighbourhood_clean, 
                       scraped_date_clean, is_complete_record
                FROM silver.silver_airbnb_listings 
                LIMIT 3
            """,
                engine,
            )
            print("Sample silver data:")
            print(sample_df.to_string())

            # Check data quality
            quality_df = pd.read_sql(
                """
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(CASE WHEN is_complete_record = true THEN 1 END) as complete_records,
                    COUNT(CASE WHEN scraped_date_clean IS NOT NULL THEN 1 END) as valid_dates,
                    COUNT(CASE WHEN property_type_clean IS NOT NULL THEN 1 END) as valid_property_types,
                    COUNT(CASE WHEN listing_neighbourhood_clean IS NOT NULL THEN 1 END) as valid_neighbourhoods
                FROM silver.silver_airbnb_listings
            """,
                engine,
            )
            print("\nData quality check:")
            print(quality_df.to_string())

        return count > 0

    except Exception as e:
        print(f"❌ Error checking silver data: {e}")
        return False


def check_gold_tables():
    """Check gold table data"""
    print("\n" + "=" * 60)
    print("CHECKING GOLD TABLE DATA")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        # Check fact_listings
        df = pd.read_sql("SELECT COUNT(*) as count FROM gold.fact_listings", engine)
        count = df["count"].iloc[0]
        print(f"fact_listings: {count} rows")

        if count > 0:
            # Check sample data
            sample_df = pd.read_sql(
                """
                SELECT listing_id, host_id, property_key, neighbourhood_key, 
                       scraped_date, scraped_year, scraped_month
                FROM gold.fact_listings 
                LIMIT 3
            """,
                engine,
            )
            print("Sample fact_listings data:")
            print(sample_df.to_string())

        # Check dimension tables
        dim_tables = ["dim_host", "dim_neighbourhood", "dim_property"]
        for table in dim_tables:
            try:
                df = pd.read_sql(f"SELECT COUNT(*) as count FROM gold.{table}", engine)
                count = df["count"].iloc[0]
                print(f"{table}: {count} rows")

                if count > 0:
                    sample_df = pd.read_sql(
                        f"SELECT * FROM gold.{table} LIMIT 2", engine
                    )
                    print(f"Sample {table} data:")
                    print(sample_df.to_string())

            except Exception as e:
                print(f"❌ Error checking {table}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error checking gold tables: {e}")
        return False


def check_snapshots():
    """Check snapshot data"""
    print("\n" + "=" * 60)
    print("CHECKING SNAPSHOT DATA")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        snapshot_tables = [
            "dim_host_snapshot",
            "dim_neighbourhood_snapshot",
            "dim_property_snapshot",
        ]
        for table in snapshot_tables:
            try:
                df = pd.read_sql(
                    f"SELECT COUNT(*) as count FROM snapshots.{table}", engine
                )
                count = df["count"].iloc[0]
                print(f"{table}: {count} rows")

                if count > 0:
                    # Check for current records (dbt_valid_to is null)
                    current_df = pd.read_sql(
                        f"""
                        SELECT COUNT(*) as current_count 
                        FROM snapshots.{table} 
                        WHERE dbt_valid_to IS NULL
                    """,
                        engine,
                    )
                    current_count = current_df["current_count"].iloc[0]
                    print(f"  Current records (dbt_valid_to IS NULL): {current_count}")

                    if current_count > 0:
                        sample_df = pd.read_sql(
                            f"""
                            SELECT * FROM snapshots.{table} 
                            WHERE dbt_valid_to IS NULL 
                            LIMIT 2
                        """,
                            engine,
                        )
                        print(f"Sample current {table} data:")
                        print(sample_df.to_string())

            except Exception as e:
                print(f"❌ Error checking {table}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error checking snapshots: {e}")
        return False


def check_mart_tables():
    """Check mart table data"""
    print("\n" + "=" * 60)
    print("CHECKING MART TABLE DATA")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        mart_tables = [
            "dm_host_neighbourhood",
            "dm_listing_neighbourhood",
            "dm_property_type",
        ]
        for table in mart_tables:
            try:
                df = pd.read_sql(f"SELECT COUNT(*) as count FROM gold.{table}", engine)
                count = df["count"].iloc[0]
                print(f"{table}: {count} rows")

                if count > 0:
                    sample_df = pd.read_sql(
                        f"SELECT * FROM gold.{table} LIMIT 3", engine
                    )
                    print(f"Sample {table} data:")
                    print(sample_df.to_string())
                else:
                    print(f"❌ {table} has no data!")

            except Exception as e:
                print(f"❌ Error checking {table}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error checking mart tables: {e}")
        return False


def diagnose_join_issues():
    """Diagnose potential join issues"""
    print("\n" + "=" * 60)
    print("DIAGNOSING JOIN ISSUES")
    print("=" * 60)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        # Check if fact_listings has valid foreign keys
        print("Checking fact_listings foreign keys...")

        # Check property_key distribution
        prop_df = pd.read_sql(
            """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN property_key IS NOT NULL THEN 1 END) as valid_property_keys,
                COUNT(DISTINCT property_key) as distinct_property_keys
            FROM gold.fact_listings
        """,
            engine,
        )
        print("Property key analysis:")
        print(prop_df.to_string())

        # Check neighbourhood_key distribution
        neigh_df = pd.read_sql(
            """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN neighbourhood_key IS NOT NULL THEN 1 END) as valid_neighbourhood_keys,
                COUNT(DISTINCT neighbourhood_key) as distinct_neighbourhood_keys
            FROM gold.fact_listings
        """,
            engine,
        )
        print("\nNeighbourhood key analysis:")
        print(neigh_df.to_string())

        # Check host_id distribution
        host_df = pd.read_sql(
            """
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN host_id IS NOT NULL THEN 1 END) as valid_host_ids,
                COUNT(DISTINCT host_id) as distinct_host_ids
            FROM gold.fact_listings
        """,
            engine,
        )
        print("\nHost ID analysis:")
        print(host_df.to_string())

        # Check date range
        date_df = pd.read_sql(
            """
            SELECT 
                MIN(scraped_date) as min_date,
                MAX(scraped_date) as max_date,
                COUNT(DISTINCT scraped_year) as distinct_years,
                COUNT(DISTINCT scraped_month) as distinct_months
            FROM gold.fact_listings
        """,
            engine,
        )
        print("\nDate range analysis:")
        print(date_df.to_string())

        return True

    except Exception as e:
        print(f"❌ Error diagnosing join issues: {e}")
        return False


def main():
    """Main function to run all diagnostic checks"""
    print("Mart Tables Diagnosis Script")
    print("=" * 60)

    # Check if database config is set
    if (
        DB_CONFIG["host"] == "YOUR_PUBLIC_IP_HERE"
        or DB_CONFIG["password"] == "YOUR_PASSWORD_HERE"
    ):
        print("❌ Please update DB_CONFIG with your actual database credentials!")
        print("Edit the DB_CONFIG dictionary at the top of this file.")
        return

    # Run all diagnostic checks
    checks = [
        check_bronze_data,
        check_silver_data,
        check_snapshots,
        check_gold_tables,
        check_mart_tables,
        diagnose_join_issues,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ DIAGNOSIS COMPLETED!")
    else:
        print("❌ DIAGNOSIS COMPLETED WITH ISSUES!")
    print("=" * 60)


if __name__ == "__main__":
    main()
