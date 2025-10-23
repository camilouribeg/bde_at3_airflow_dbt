#!/usr/bin/env python3
"""
Question 1 Visualizations - Top/Bottom 3 LGAs with Demographics
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Set style
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")


def create_q1_plots():
    """Create Question 1 visualizations"""
    print("🎯 QUESTION 1 VISUALIZATIONS")
    print("=" * 50)

    # Load Question 1 data
    df = pd.read_csv("data/q1_top_bottom_lgas_demographics.csv")

    print("📊 Data Overview:")
    print(f"   📈 Records: {len(df)}")
    print(f"   📋 Columns: {list(df.columns)}")
    print()

    # Create plots directory
    os.makedirs("plots", exist_ok=True)

    # PLOT 1: Revenue Comparison Bar Chart
    plt.figure(figsize=(12, 8))
    colors = [
        "#2E8B57" if group == "TOP_3" else "#DC143C"
        for group in df["performance_group"]
    ]
    bars = plt.bar(
        df["lga_name"], df["avg_revenue_per_active_listing"], color=colors, alpha=0.8
    )

    plt.title(
        "Question 1: Revenue per Active Listing - Top 3 vs Bottom 3 LGAs",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("LGA Name", fontsize=12, fontweight="bold")
    plt.ylabel("Average Revenue per Active Listing ($)", fontsize=12, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.3)

    # Add value labels on bars
    for bar, value in zip(bars, df["avg_revenue_per_active_listing"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 50,
            f"${value:,.0f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#2E8B57", label="Top 3 LGAs"),
        Patch(facecolor="#DC143C", label="Bottom 3 LGAs"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    plt.savefig("plots/q1_revenue_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✅ Plot 1: Revenue Comparison Bar Chart")
    print("   📁 Saved: plots/q1_revenue_comparison.png")
    print()

    # PLOT 2: Demographics Comparison (Male/Female Percentages)
    plt.figure(figsize=(14, 8))

    # Create grouped bar chart
    x = np.arange(len(df))
    width = 0.35

    bars1 = plt.bar(
        x - width / 2,
        df["male_percentage"],
        width,
        label="Male %",
        color="#4A90E2",
        alpha=0.8,
    )
    bars2 = plt.bar(
        x + width / 2,
        df["female_percentage"],
        width,
        label="Female %",
        color="#E24A90",
        alpha=0.8,
    )

    plt.title(
        "Question 1: Gender Distribution - Top 3 vs Bottom 3 LGAs",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("LGA Name", fontsize=12, fontweight="bold")
    plt.ylabel("Percentage (%)", fontsize=12, fontweight="bold")
    plt.xticks(x, df["lga_name"], rotation=45, ha="right")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.5,
                f"{height:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    plt.tight_layout()
    plt.savefig("plots/q1_gender_distribution.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✅ Plot 2: Gender Distribution Comparison")
    print("   📁 Saved: plots/q1_gender_distribution.png")
    print()

    # PLOT 3: Age vs Revenue Scatter Plot
    plt.figure(figsize=(12, 8))
    colors = [
        "#2E8B57" if group == "TOP_3" else "#DC143C"
        for group in df["performance_group"]
    ]
    scatter = plt.scatter(
        df["median_age_persons"],
        df["avg_revenue_per_active_listing"],
        c=colors,
        s=200,
        alpha=0.7,
        edgecolors="black",
        linewidth=1,
    )

    plt.title(
        "Question 1: Age vs Revenue Correlation - Top 3 vs Bottom 3 LGAs",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("Median Age (years)", fontsize=12, fontweight="bold")
    plt.ylabel("Average Revenue per Active Listing ($)", fontsize=12, fontweight="bold")
    plt.grid(True, alpha=0.3)

    # Add LGA labels
    for i, row in df.iterrows():
        plt.annotate(
            row["lga_name"],
            (row["median_age_persons"], row["avg_revenue_per_active_listing"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
        )

    # Add legend
    legend_elements = [
        Patch(facecolor="#2E8B57", label="Top 3 LGAs"),
        Patch(facecolor="#DC143C", label="Bottom 3 LGAs"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    plt.savefig("plots/q1_age_vs_revenue.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✅ Plot 3: Age vs Revenue Scatter Plot")
    print("   📁 Saved: plots/q1_age_vs_revenue.png")
    print()

    # PLOT 4: Population Size Comparison
    plt.figure(figsize=(12, 8))
    colors = [
        "#2E8B57" if group == "TOP_3" else "#DC143C"
        for group in df["performance_group"]
    ]
    bars = plt.bar(df["lga_name"], df["total_population"], color=colors, alpha=0.8)

    plt.title(
        "Question 1: Total Population - Top 3 vs Bottom 3 LGAs",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("LGA Name", fontsize=12, fontweight="bold")
    plt.ylabel("Total Population", fontsize=12, fontweight="bold")
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", alpha=0.3)

    # Add value labels
    for bar, value in zip(bars, df["total_population"]):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1000,
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # Add legend
    legend_elements = [
        Patch(facecolor="#2E8B57", label="Top 3 LGAs"),
        Patch(facecolor="#DC143C", label="Bottom 3 LGAs"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    plt.savefig("plots/q1_population_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("✅ Plot 4: Population Size Comparison")
    print("   📁 Saved: plots/q1_population_comparison.png")
    print()

    print("🎯 QUESTION 1 PLOTS COMPLETED!")
    print("=" * 40)
    print("📁 All plots saved in: plots/")
    print("📊 4 different visualizations created")
    print("🎨 Ready for review and selection!")


if __name__ == "__main__":
    create_q1_plots()
