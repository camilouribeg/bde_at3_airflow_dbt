#!/usr/bin/env python3
"""
Business Question 2 Analysis: Age vs Revenue Correlation (CORRECTED)
Analyze the correlation between median age of neighbourhoods and revenue generated per active listing.
Note: The 'listing_neighbourhood' field actually contains LGA names, not individual suburbs.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


def load_question2_data():
    """Load Question 2 data"""
    print("📊 Loading Question 2 Data...")

    # Load the age vs revenue data
    age_revenue_df = pd.read_csv("data/q2_age_revenue_data.csv")

    print(f"   📈 LGAs with age and revenue data: {len(age_revenue_df)}")
    print(
        f"   📊 Age range: {age_revenue_df['median_age_persons'].min():.1f} - {age_revenue_df['median_age_persons'].max():.1f} years"
    )
    print(
        f"   💰 Revenue range: ${age_revenue_df['avg_revenue_per_active_listing'].min():,.0f} - ${age_revenue_df['avg_revenue_per_active_listing'].max():,.0f}"
    )

    return age_revenue_df


def explain_data_structure():
    """Explain the data structure and why we use LGA level"""
    print("\n🔍 DATA STRUCTURE EXPLANATION")
    print("=" * 60)

    print(
        "📋 QUESTION: 'Is there a correlation between the median age of a neighbourhood"
    )
    print(
        "   (from Census data) and the revenue generated per active listing in that neighbourhood?'"
    )
    print("   📅 DATA PERIOD: 12 months (May 2020 - April 2021)")
    print()

    print("🏗️ DATA ARCHITECTURE ANALYSIS:")
    print(
        "   • 'listing_neighbourhood' in dm_listing_neighbourhood = LGA names (not individual suburbs)"
    )
    print("   • Examples: 'MOSMAN', 'HUNTERS HILL', 'WOOLLAHRA' (these are LGAs)")
    print("   • Census age data (median_age_persons) is available at LGA level")
    print("   • Individual suburb age data is NOT available in Census")
    print()

    print("✅ WHY LGA LEVEL IS APPROPRIATE:")
    print("   • Census data provides age demographics at LGA level")
    print("   • 'listing_neighbourhood' field contains LGA names")
    print("   • This is the finest granularity available for age-revenue correlation")
    print("   • LGA represents a meaningful geographic unit for analysis")
    print()

    print("🔄 ALTERNATIVE APPROACH (if suburb-level age data existed):")
    print("   • Would need: suburb_name → age mapping")
    print("   • Would join: dm_listing_neighbourhood → dim_suburb → age_data")
    print("   • Current limitation: Census age data only available at LGA level")


def calculate_correlation_simple(age_revenue_df):
    """Calculate correlation between age and revenue using simple method"""
    print("\n📊 CORRELATION ANALYSIS")
    print("=" * 50)

    # Remove any rows with missing data
    clean_df = age_revenue_df.dropna(
        subset=["median_age_persons", "avg_revenue_per_active_listing"]
    )

    if len(clean_df) < 2:
        print("❌ Not enough data points for correlation analysis")
        return None, None

    # Calculate Pearson correlation coefficient manually
    age = clean_df["median_age_persons"]
    revenue = clean_df["avg_revenue_per_active_listing"]

    # Calculate means
    age_mean = age.mean()
    revenue_mean = revenue.mean()

    # Calculate correlation coefficient
    numerator = ((age - age_mean) * (revenue - revenue_mean)).sum()
    age_var = ((age - age_mean) ** 2).sum()
    revenue_var = ((revenue - revenue_mean) ** 2).sum()

    correlation_coef = numerator / np.sqrt(age_var * revenue_var)

    print(f"📈 Pearson Correlation Coefficient: {correlation_coef:.4f}")
    print(f"📋 Sample size: {len(clean_df)} LGAs")
    print(f"📊 Analysis level: LGA (Local Government Area)")

    # Interpret correlation strength
    if abs(correlation_coef) >= 0.7:
        strength = "strong"
    elif abs(correlation_coef) >= 0.5:
        strength = "moderate"
    elif abs(correlation_coef) >= 0.3:
        strength = "weak"
    else:
        strength = "very weak"

    direction = "positive" if correlation_coef > 0 else "negative"

    print(f"\n💡 CORRELATION INTERPRETATION:")
    print(f"   • Strength: {strength} ({abs(correlation_coef):.3f})")
    print(f"   • Direction: {direction}")
    print(f"   • Geographic level: LGA (neighbourhood-level equivalent)")

    return correlation_coef, len(clean_df)


def create_analysis_tables(age_revenue_df):
    """Create analysis tables for Question 2"""
    print("\n📋 ANALYSIS TABLES")
    print("=" * 50)

    # Table 1: Age vs Revenue Summary Statistics
    print("\n📊 TABLE 1: Age vs Revenue Summary Statistics (LGA Level)")
    print("-" * 60)

    summary_stats = age_revenue_df[
        ["median_age_persons", "avg_revenue_per_active_listing"]
    ].describe()
    print(summary_stats.round(2))

    # Table 2: Top 5 by Age and Revenue
    print("\n📊 TABLE 2: Top 5 LGAs by Median Age")
    print("-" * 60)
    top_age = age_revenue_df.nlargest(5, "median_age_persons")[
        ["lga_name", "median_age_persons", "avg_revenue_per_active_listing"]
    ]
    print(top_age.to_string(index=False))

    print("\n📊 TABLE 3: Top 5 LGAs by Revenue per Listing")
    print("-" * 60)
    top_revenue = age_revenue_df.nlargest(5, "avg_revenue_per_active_listing")[
        ["lga_name", "median_age_persons", "avg_revenue_per_active_listing"]
    ]
    print(top_revenue.to_string(index=False))

    # Table 4: Age-Revenue Relationship Analysis
    print("\n📊 TABLE 4: Age-Revenue Relationship Analysis")
    print("-" * 60)

    # Create age groups
    age_revenue_df["age_group"] = pd.cut(
        age_revenue_df["median_age_persons"],
        bins=[0, 35, 40, 45, 100],
        labels=["Young (≤35)", "Middle (36-40)", "Mature (41-45)", "Senior (45+)"],
    )

    age_group_analysis = (
        age_revenue_df.groupby("age_group")
        .agg(
            {
                "avg_revenue_per_active_listing": ["count", "mean", "std"],
                "median_age_persons": "mean",
            }
        )
        .round(2)
    )

    print(age_group_analysis)

    # Table 5: Detailed Age-Revenue Data
    print("\n📊 TABLE 5: All LGAs - Age vs Revenue")
    print("-" * 80)
    detailed_data = age_revenue_df[
        ["lga_name", "median_age_persons", "avg_revenue_per_active_listing"]
    ].copy()
    detailed_data["avg_revenue_per_active_listing"] = detailed_data[
        "avg_revenue_per_active_listing"
    ].apply(lambda x: f"${x:,.0f}")
    print(detailed_data.to_string(index=False))

    return age_group_analysis


def generate_insights(correlation_coef, sample_size, age_revenue_df):
    """Generate key insights from Question 2 analysis"""
    print("\n💡 KEY INSIGHTS FROM QUESTION 2 ANALYSIS")
    print("=" * 60)

    print(
        "🎯 QUESTION: Is there a correlation between median age and revenue per listing?"
    )
    print(
        "📊 ANALYSIS LEVEL: LGA (Local Government Area) - equivalent to neighbourhood level"
    )
    print()

    # Correlation insights
    print("📊 CORRELATION FINDINGS:")
    if abs(correlation_coef) >= 0.3:
        direction = "positive" if correlation_coef > 0 else "negative"
        strength = (
            "strong"
            if abs(correlation_coef) >= 0.7
            else "moderate" if abs(correlation_coef) >= 0.5 else "weak"
        )
        print(f"   ✅ YES - There is a {strength} {direction} correlation")
        print(f"   📈 Correlation coefficient: {correlation_coef:.3f}")
        print(f"   🏗️ Analysis level: LGA (neighbourhood-level equivalent)")
    else:
        print(f"   ❌ NO - There is no significant correlation")
        print(f"   📈 Correlation coefficient: {correlation_coef:.3f} (very weak)")

    # Business insights
    print("\n💼 BUSINESS INSIGHTS:")
    if correlation_coef > 0.3:
        print("   • Older LGAs tend to generate higher revenue per listing")
        print("   • Age demographics may be a predictor of Airbnb performance")
        print("   • Consider targeting properties in LGAs with older populations")
        print(
            "   • Mature LGAs may have higher disposable income for short-term rentals"
        )
        print("   • LGA-level age demographics correlate with revenue performance")
    elif correlation_coef < -0.3:
        print("   • Younger LGAs tend to generate higher revenue per listing")
        print("   • Youth demographics may drive Airbnb demand")
        print("   • Consider targeting properties in LGAs with younger populations")
        print("   • Young LGAs may have higher tourism and business travel")
    else:
        print("   • Age is not a strong predictor of revenue per listing")
        print("   • Other factors (location, amenities, etc.) are more important")
        print("   • Focus on non-demographic factors for revenue optimization")
        print("   • Geographic location and property features matter more than age")

    # Data quality insights
    print("\n📊 DATA QUALITY INSIGHTS:")
    print(f"   • Analysis based on {sample_size} LGAs with complete data")
    print(
        f"   • Age range: {age_revenue_df['median_age_persons'].min():.0f}-{age_revenue_df['median_age_persons'].max():.0f} years"
    )
    print(
        f"   • Revenue range: ${age_revenue_df['avg_revenue_per_active_listing'].min():,.0f}-${age_revenue_df['avg_revenue_per_active_listing'].max():,.0f}"
    )
    print(f"   • Geographic granularity: LGA level (appropriate for Census age data)")

    # Specific examples
    print("\n🔍 SPECIFIC EXAMPLES:")
    oldest_lga = age_revenue_df.loc[age_revenue_df["median_age_persons"].idxmax()]
    youngest_lga = age_revenue_df.loc[age_revenue_df["median_age_persons"].idxmin()]

    print(
        f"   • Oldest LGA: {oldest_lga['lga_name']} (age {oldest_lga['median_age_persons']:.0f}, revenue ${oldest_lga['avg_revenue_per_active_listing']:,.0f})"
    )
    print(
        f"   • Youngest LGA: {youngest_lga['lga_name']} (age {youngest_lga['median_age_persons']:.0f}, revenue ${youngest_lga['avg_revenue_per_active_listing']:,.0f})"
    )


def save_analysis_results(correlation_coef, sample_size, age_group_analysis):
    """Save analysis results to files"""
    print("\n💾 Saving Analysis Results...")

    os.makedirs("analysis", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save correlation results
    correlation_results = pd.DataFrame(
        {
            "Metric": [
                "Correlation Coefficient",
                "Sample Size",
                "Analysis Level",
                "Interpretation",
            ],
            "Value": [
                correlation_coef,
                sample_size,
                "LGA (neighbourhood-level equivalent)",
                f"{'Strong' if abs(correlation_coef) >= 0.7 else 'Moderate' if abs(correlation_coef) >= 0.5 else 'Weak' if abs(correlation_coef) >= 0.3 else 'Very Weak'} {'Positive' if correlation_coef > 0 else 'Negative'}",
            ],
        }
    )

    correlation_results.to_csv(
        f"analysis/q2_correlation_results_corrected_{timestamp}.csv", index=False
    )
    age_group_analysis.to_csv(
        f"analysis/q2_age_group_analysis_corrected_{timestamp}.csv"
    )

    print(f"✅ Analysis results saved to analysis/ folder")


def main():
    """Main analysis function"""
    print("🎯 BUSINESS QUESTION 2 ANALYSIS: Age vs Revenue Correlation (CORRECTED)")
    print("=" * 80)

    # Explain data structure
    explain_data_structure()

    # Load data
    age_revenue_df = load_question2_data()

    # Calculate correlation
    correlation_coef, sample_size = calculate_correlation_simple(age_revenue_df)

    if correlation_coef is not None:
        # Create analysis tables
        age_group_analysis = create_analysis_tables(age_revenue_df)

        # Generate insights
        generate_insights(correlation_coef, sample_size, age_revenue_df)

        # Save results
        save_analysis_results(correlation_coef, sample_size, age_group_analysis)

    print(f"\n✅ Question 2 analysis completed!")
    print(f"   📁 Analysis files saved in: business_questions_final/analysis/")
    print(f"   🎯 Ready for Question 3!")


if __name__ == "__main__":
    main()
