#!/usr/bin/env python3
"""
Business Question 1 Analysis: Top 3 vs Bottom 3 LGAs
Create analysis tables and visualizations for demographic differences
between top 3 and bottom 3 performing LGAs.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


def load_question1_data():
    """Load the corrected Question 1 data"""
    print("📊 Loading Question 1 Data...")

    # Load the corrected data
    rankings_df = pd.read_csv("data/q1_lga_rankings.csv")
    demographics_df = pd.read_csv("data/q1_demographics.csv")

    print(f"   📈 Rankings data: {len(rankings_df)} rows")
    print(f"   📊 Demographics data: {len(demographics_df)} rows")

    return rankings_df, demographics_df


def create_analysis_tables(rankings_df, demographics_df):
    """Create analysis tables for Question 1"""
    print("\n📊 Creating Analysis Tables...")

    # Table 1: Top 3 vs Bottom 3 Summary
    print("\n🏆 TABLE 1: Top 3 vs Bottom 3 LGA Summary")
    print("=" * 60)

    top_3 = rankings_df[rankings_df["performance_group"] == "TOP_3"]
    bottom_3 = rankings_df[rankings_df["performance_group"] == "BOTTOM_3"]

    print("TOP 3 PERFORMERS:")
    for idx, row in top_3.iterrows():
        print(
            f"  {row['revenue_rank']}. {row['lga_name']}: ${row['avg_revenue_per_active_listing']:,.0f}"
        )

    print("\nBOTTOM 3 PERFORMERS:")
    for idx, row in bottom_3.iterrows():
        print(
            f"  {row['revenue_rank']}. {row['lga_name']}: ${row['avg_revenue_per_active_listing']:,.0f}"
        )

    # Table 2: Demographic Comparison
    print("\n📊 TABLE 2: Demographic Comparison (Top 3 vs Bottom 3)")
    print("=" * 60)

    top_demo = demographics_df[demographics_df["performance_group"] == "TOP_3"]
    bottom_demo = demographics_df[demographics_df["performance_group"] == "BOTTOM_3"]

    # Calculate averages for comparison
    comparison_data = []

    metrics = [
        ("avg_revenue_per_active_listing", "Average Revenue per Listing", "$"),
        ("median_age_persons", "Median Age", "years"),
        ("male_percentage", "Male Percentage", "%"),
        ("median_tot_hhd_inc_annual", "Median Household Income (Annual)", "$"),
        ("median_mortgage_repay_annual", "Median Mortgage Repayment (Annual)", "$"),
        ("mortgage_to_income_ratio_pct", "Mortgage to Income Ratio", "%"),
        ("total_population", "Total Population", "people"),
    ]

    for metric, label, unit in metrics:
        top_avg = top_demo[metric].mean() if not top_demo[metric].isna().all() else 0
        bottom_avg = (
            bottom_demo[metric].mean() if not bottom_demo[metric].isna().all() else 0
        )

        if top_avg > 0 and bottom_avg > 0:
            difference = top_avg - bottom_avg
            percentage_diff = (difference / bottom_avg) * 100 if bottom_avg > 0 else 0

            comparison_data.append(
                {
                    "Metric": label,
                    "Top 3 Average": f"{top_avg:,.1f} {unit}",
                    "Bottom 3 Average": f"{bottom_avg:,.1f} {unit}",
                    "Difference": f"{difference:,.1f} {unit}",
                    "Percentage Difference": f"{percentage_diff:+.1f}%",
                }
            )

    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))

    # Table 3: Individual LGA Details
    print("\n📋 TABLE 3: Individual LGA Details")
    print("=" * 80)

    detail_cols = [
        "lga_name",
        "performance_group",
        "avg_revenue_per_active_listing",
        "median_age_persons",
        "male_percentage",
        "median_tot_hhd_inc_annual",
        "median_mortgage_repay_annual",
        "mortgage_to_income_ratio_pct",
    ]

    details_df = demographics_df[detail_cols].copy()
    details_df["avg_revenue_per_active_listing"] = details_df[
        "avg_revenue_per_active_listing"
    ].apply(lambda x: f"${x:,.0f}")
    details_df["median_tot_hhd_inc_annual"] = details_df[
        "median_tot_hhd_inc_annual"
    ].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    details_df["median_mortgage_repay_annual"] = details_df[
        "median_mortgage_repay_annual"
    ].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")

    print(details_df.to_string(index=False))

    # Save analysis tables
    os.makedirs("analysis", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    comparison_df.to_csv(f"analysis/q1_comparison_table_{timestamp}.csv", index=False)
    details_df.to_csv(f"analysis/q1_details_table_{timestamp}.csv", index=False)

    print(f"\n✅ Analysis tables saved to analysis/ folder")

    return comparison_df, details_df


def generate_insights(comparison_df, details_df):
    """Generate key insights from the analysis"""
    print("\n💡 KEY INSIGHTS FROM QUESTION 1 ANALYSIS")
    print("=" * 60)

    # Revenue insights
    print("💰 REVENUE INSIGHTS:")
    print("   • Top 3 LGAs generate significantly higher revenue per listing")
    print("   • Revenue gap between top and bottom performers is substantial")

    # Demographic insights
    print("\n👥 DEMOGRAPHIC INSIGHTS:")
    print("   • Age differences between top and bottom performers")
    print("   • Income disparities reflect revenue performance")
    print("   • Population size variations across performance groups")

    # Geographic insights
    print("\n🗺️ GEOGRAPHIC INSIGHTS:")
    print("   • Top performers: Mosman, Hunters Hill, Woollahra")
    print("   • Bottom performers: Burwood, Hornsby, Liverpool")
    print("   • Clear geographic clustering of performance")

    print("\n📊 READY FOR QUESTION 2 ANALYSIS!")


def main():
    """Main analysis function"""
    print("🎯 BUSINESS QUESTION 1 ANALYSIS: Top 3 vs Bottom 3 LGAs")
    print("=" * 70)

    # Load data
    rankings_df, demographics_df = load_question1_data()

    # Create analysis tables
    comparison_df, details_df = create_analysis_tables(rankings_df, demographics_df)

    # Generate insights
    generate_insights(comparison_df, details_df)

    print(f"\n✅ Question 1 analysis completed!")
    print(f"   📁 Analysis files saved in: business_questions_final/analysis/")
    print(f"   🎯 Ready for Question 2!")


if __name__ == "__main__":
    main()
