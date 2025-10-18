import psycopg2
import pandas as pd
from sqlalchemy import create_engine
import logging

# Database connection parameters
# TODO: Update these with your actual database details
DB_CONFIG = {
    "host": "YOUR_PUBLIC_IP_HERE",  # Replace with your PostgreSQL public IP
    "port": 5432,
    "database": "postgres",  # or your database name
    "user": "postgres",  # or your username
    "password": "YOUR_PASSWORD_HERE",  # Replace with your password
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


def check_database_connection():
    """Test database connection"""
    print("=" * 50)
    print("CHECKING DATABASE CONNECTION")
    print("=" * 50)

    conn = get_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False


def check_schemas():
    """Check if required schemas exist"""
    print("\n" + "=" * 50)
    print("CHECKING SCHEMAS")
    print("=" * 50)

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('bronze', 'silver', 'gold', 'snapshots')
            ORDER BY schema_name;
        """
        )

        schemas = cursor.fetchall()
        required_schemas = ["bronze", "silver", "gold", "snapshots"]

        print("Required schemas:", required_schemas)
        print("Existing schemas:", [schema[0] for schema in schemas])

        missing_schemas = set(required_schemas) - set([schema[0] for schema in schemas])

        if missing_schemas:
            print(f"❌ Missing schemas: {missing_schemas}")
            return False
        else:
            print("✅ All required schemas exist!")
            return True

    except Exception as e:
        print(f"❌ Error checking schemas: {e}")
        return False
    finally:
        conn.close()


def check_bronze_tables():
    """Check if bronze tables exist and have correct structure"""
    print("\n" + "=" * 50)
    print("CHECKING BRONZE TABLES")
    print("=" * 50)

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Check if bronze tables exist
        bronze_tables = [
            "raw_census_g01",
            "raw_census_g02",
            "raw_lga_mapping",
            "raw_airbnb_listings",
        ]

        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'bronze' 
            AND table_name IN %s
            ORDER BY table_name;
        """,
            (tuple(bronze_tables),),
        )

        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"Required bronze tables: {bronze_tables}")
        print(f"Existing bronze tables: {existing_tables}")

        missing_tables = set(bronze_tables) - set(existing_tables)
        if missing_tables:
            print(f"❌ Missing bronze tables: {missing_tables}")
            return False

        # Check table structures
        for table in bronze_tables:
            print(f"\n--- Checking {table} structure ---")
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'bronze' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """,
                (table,),
            )

            columns = cursor.fetchall()
            print(f"Columns in {table}: {len(columns)}")

            # Show first few columns as sample
            for i, (col_name, data_type, nullable) in enumerate(columns[:5]):
                print(
                    f"  {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})"
                )

            if len(columns) > 5:
                print(f"  ... and {len(columns) - 5} more columns")

        print("✅ All bronze tables exist with proper structure!")
        return True

    except Exception as e:
        print(f"❌ Error checking bronze tables: {e}")
        return False
    finally:
        conn.close()


def check_table_data():
    """Check if tables have data"""
    print("\n" + "=" * 50)
    print("CHECKING TABLE DATA")
    print("=" * 50)

    engine = get_sqlalchemy_engine()
    if not engine:
        return False

    try:
        bronze_tables = [
            "raw_census_g01",
            "raw_census_g02",
            "raw_lga_mapping",
            "raw_airbnb_listings",
        ]

        for table in bronze_tables:
            try:
                df = pd.read_sql(
                    f"SELECT COUNT(*) as count FROM bronze.{table}", engine
                )
                count = df["count"].iloc[0]
                print(f"{table}: {count} rows")

                if count > 0:
                    # Show sample data
                    sample_df = pd.read_sql(
                        f"SELECT * FROM bronze.{table} LIMIT 3", engine
                    )
                    print(f"  Sample columns: {list(sample_df.columns)[:5]}...")

            except Exception as e:
                print(f"❌ Error checking {table}: {e}")
                return False

        print("✅ Data check completed!")
        return True

    except Exception as e:
        print(f"❌ Error checking table data: {e}")
        return False


def run_custom_query(query):
    """Run a custom SQL query"""
    print(f"\nRunning query: {query}")

    engine = get_sqlalchemy_engine()
    if not engine:
        return None

    try:
        df = pd.read_sql(query, engine)
        print(f"Query returned {len(df)} rows")
        return df
    except Exception as e:
        print(f"❌ Error running query: {e}")
        return None


def create_bronze_tables():
    """Create bronze tables if they don't exist"""
    print("\n" + "=" * 50)
    print("CREATING BRONZE TABLES")
    print("=" * 50)

    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()

        # Read and execute the SQL file
        with open("create_bronze_tables.sql", "r") as f:
            sql_content = f.read()

        cursor.execute(sql_content)
        conn.commit()

        print("✅ Bronze tables created successfully!")
        return True

    except Exception as e:
        print(f"❌ Error creating bronze tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main function to run all checks"""
    print("PostgreSQL Database Checker")
    print("=" * 50)

    # Check if database config is set
    if (
        DB_CONFIG["host"] == "YOUR_PUBLIC_IP_HERE"
        or DB_CONFIG["password"] == "YOUR_PASSWORD_HERE"
    ):
        print("❌ Please update DB_CONFIG with your actual database credentials!")
        print("Edit the DB_CONFIG dictionary at the top of this file.")
        return

    # Run all checks
    checks = [
        check_database_connection,
        check_schemas,
        check_bronze_tables,
        check_table_data,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL CHECKS PASSED! Database is ready for Airflow.")
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues before running Airflow.")
    print("=" * 50)


if __name__ == "__main__":
    main()
