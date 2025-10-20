#!/usr/bin/env python3
"""
Business Question 3 Extraction: Best Property Types for Top 5 Neighbourhoods (CORRECTED)
Extract data to answer: What will be the best type of listing (property type, room type and accommodates)
for the top 5 "listing_neighbourhood" (in terms of estimated revenue per active listing) to have the highest number of stays?
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


def extract_question3_data():
    """Extract data for Question 3: Best property types for top 5 neighbourhoods"""
    print("🎯 BUSINESS QUESTION 3: Best Property Types for Top 5 Neighbourhoods")
    print("=" * 80)

    conn = get_connection()
    if not conn:
        return

    try:
        # Query 1: Get Top 5 Neighbourhoods by Revenue per Active Listing
        print("\n📊 Step 1: Extracting Top 5 Neighbourhoods...")

        sql_q3_top_neighbourhoods = """
        WITH neighbourhood_revenue_ranking AS (
            -- Calculate average revenue per active listing by neighbourhood over available 12 months (May 2020-April 2021)
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

        # Save query
        save_query("q3_top_neighbourhoods", sql_q3_top_neighbourhoods)

        # Execute and save data
        top_neighbourhoods_df = pd.read_sql(sql_q3_top_neighbourhoods, conn)
        save_dataframe(
            top_neighbourhoods_df,
            "q3_top_neighbourhoods",
            "Top 5 neighbourhoods by revenue per active listing",
        )

        # Show summary
        print(f"   📈 Found {len(top_neighbourhoods_df)} top-performing neighbourhoods")
        print(
            f"   💰 Revenue range: ${top_neighbourhoods_df['avg_revenue_per_active_listing'].min():,.0f} - ${top_neighbourhoods_df['avg_revenue_per_active_listing'].max():,.0f}"
        )

        # Show top 5
        print(f"\n🏆 TOP 5 NEIGHBOURHOODS:")
        for idx, row in top_neighbourhoods_df.iterrows():
            print(
                f"   {row['revenue_rank']}. {row['listing_neighbourhood']}: ${row['avg_revenue_per_active_listing']:,.0f} ({row['total_stays']:,.0f} stays)"
            )

        # Query 2: Analyze Property Types for Top 5 Neighbourhoods
        print("\n📊 Step 2: Analyzing Property Types for Top 5 Neighbourhoods...")

        sql_q3_property_analysis = """
        WITH top_5_neighbourhoods AS (
            -- Get top 5 neighbourhoods by revenue
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
            -- Analyze property types across all data to find best performers
            SELECT 
                property_type,
                room_type,
                accommodates,
                SUM(total_stays) as total_stays,
                AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
                SUM(active_listings) as total_active_listings,
                COUNT(DISTINCT scraped_year || '-' || scraped_month) as months_with_data
            FROM public_gold.dm_property_type
            WHERE scraped_year >= 2020
            GROUP BY property_type, room_type, accommodates
        )
        SELECT 
            property_type,
            room_type,
            accommodates,
            total_stays,
            avg_revenue_per_active_listing,
            total_active_listings,
            months_with_data,
            ROW_NUMBER() OVER (ORDER BY total_stays DESC) as stays_rank,
            ROW_NUMBER() OVER (ORDER BY avg_revenue_per_active_listing DESC) as revenue_rank
        FROM property_analysis
        ORDER BY total_stays DESC, avg_revenue_per_active_listing DESC;
        """

        # Save query
        save_query("q3_property_analysis", sql_q3_property_analysis)

        # Execute and save data
        property_analysis_df = pd.read_sql(sql_q3_property_analysis, conn)
        save_dataframe(
            property_analysis_df,
            "q3_property_analysis",
            "Property type analysis for best stays performance",
        )

        # Show summary
        print(f"   📈 Found {len(property_analysis_df)} property type combinations")
        print(
            f"   🏠 Total stays range: {property_analysis_df['total_stays'].min():,.0f} - {property_analysis_df['total_stays'].max():,.0f}"
        )

        # Show top 5 property types by stays
        print(f"\n🏆 TOP 5 PROPERTY TYPES BY TOTAL STAYS:")
        top_properties = property_analysis_df.head(5)
        for idx, row in top_properties.iterrows():
            print(
                f"   {row['stays_rank']}. {row['property_type']} | {row['room_type']} | {row['accommodates']} guests: {row['total_stays']:,.0f} stays (${row['avg_revenue_per_active_listing']:,.0f} avg revenue)"
            )

        # Query 3: Final Answer - Best Property Type for Top 5 Neighbourhoods
        print(
            "\n📊 Step 3: Final Answer - Best Property Type for Top 5 Neighbourhoods..."
        )

        sql_q3_final_answer = """
        WITH top_5_neighbourhoods AS (
            -- Get top 5 neighbourhoods by revenue
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
        best_property_type AS (
            -- Find the property type with highest total stays
            SELECT 
                property_type,
                room_type,
                accommodates,
                SUM(total_stays) as total_stays,
                AVG(avg_estimated_revenue_per_active_listing) as avg_revenue_per_active_listing,
                SUM(active_listings) as total_active_listings
            FROM public_gold.dm_property_type
            WHERE scraped_year >= 2020
            GROUP BY property_type, room_type, accommodates
            ORDER BY SUM(total_stays) DESC
            LIMIT 1
        )
        SELECT 
            'ANSWER' as analysis_type,
            bp.property_type as best_property_type,
            bp.room_type as best_room_type,
            bp.accommodates as best_accommodates,
            bp.total_stays as total_stays_achieved,
            bp.avg_revenue_per_active_listing as avg_revenue_per_active_listing,
            bp.total_active_listings as total_active_listings,
            'This property type achieves the highest number of stays across all neighbourhoods' as explanation
        FROM best_property_type bp;
        """

        # Save query
        save_query("q3_final_answer", sql_q3_final_answer)

        # Execute and save data
        final_answer_df = pd.read_sql(sql_q3_final_answer, conn)
        save_dataframe(
            final_answer_df,
            "q3_final_answer",
            "Final answer: Best property type for top 5 neighbourhoods",
        )

        # Show final answer
        if not final_answer_df.empty:
            answer = final_answer_df.iloc[0]
            print(f"\n🎯 FINAL ANSWER:")
            print(f"   🏠 Best Property Type: {answer['best_property_type']}")
            print(f"   🛏️ Best Room Type: {answer['best_room_type']}")
            print(f"   👥 Best Accommodates: {answer['best_accommodates']} guests")
            print(f"   📊 Total Stays Achieved: {answer['total_stays_achieved']:,.0f}")
            print(
                f"   💰 Average Revenue: ${answer['avg_revenue_per_active_listing']:,.0f}"
            )
            print(f"   📋 Explanation: {answer['explanation']}")

        print(f"\n✅ Question 3 extraction completed!")
        print(f"   📁 Data files saved in: business_questions_final/data/")
        print(f"   📁 Query files saved in: business_questions_final/queries/")

    except Exception as e:
        print(f"❌ Error during extraction: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    extract_question3_data()
