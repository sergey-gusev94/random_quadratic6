import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# --- 1. Generate Random Data ---
np.random.seed(42)  # for reproducibility
num_instances = 20
reformulations = ["BigM", "Hull", "Experimental"]
data = []

for i in range(1, num_instances + 1):
    instance_name = f"P{i}"
    # Primal bound should be the same for the same instance
    primal_bound = np.random.uniform(50, 500)

    for reform_type in reformulations:
        # Simulate dual bounds (lower for minimization problems)
        if reform_type == "BigM":
            # BigM often has larger gaps
            dual_bound = primal_bound * np.random.uniform(0.6, 0.85)
        elif reform_type == "Hull":
            # Hull often has tighter gaps
            dual_bound = primal_bound * np.random.uniform(0.8, 0.98)
        else:  # Experimental
            # Experimental could be more variable
            dual_bound = primal_bound * np.random.uniform(0.7, 0.95)

        # Ensure dual_bound <= primal_bound (for minimization)
        dual_bound = min(dual_bound, primal_bound * 0.999)  # to avoid zero gap artificially often

        abs_gap = primal_bound - dual_bound
        # Robust relative gap calculation to avoid division by zero or very small primal
        if abs(primal_bound) > 1e-6:
            rel_gap = abs_gap / abs(primal_bound)
        elif abs(dual_bound) > 1e-6:  # Use dual bound if primal is near zero
            rel_gap = abs_gap / abs(dual_bound)
        else:  # If both are near zero, gap is effectively zero or undefined
            rel_gap = 0.0 if abs_gap < 1e-6 else np.nan  # Or handle as a special case

        solve_time_relax = np.random.uniform(0.1, 5.0)
        solve_time_minlp = np.random.uniform(1.0, 60.0)

        data.append(
            {
                "Problem_Instance": instance_name,
                "Reformulation": reform_type,
                "Primal_Bound": primal_bound,
                "Dual_Bound": dual_bound,
                "Abs_Gap": abs_gap,
                "Rel_Gap": rel_gap,
                "Solve_Time_Relax": solve_time_relax,
                "Solve_Time_MINLP": solve_time_minlp,
            }
        )

df = pd.DataFrame(data)
df = df.dropna(subset=["Rel_Gap"])  # Drop rows where Rel_Gap might be NaN

print("Sample Data Head:")
print(df.head())
print("\n--- Visualizations ---")

# --- 2. Visualization Examples ---

# Option 1: Box Plots (or Violin Plots) of Gaps
print("\n1. Box Plot & Violin Plot")
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
sns.boxplot(x="Reformulation", y="Rel_Gap", data=df)
plt.title("Box Plot: Relative Relaxation Gap by Reformulation")
plt.ylabel("Relative Relaxation Gap")
plt.xlabel("Reformulation Type")
plt.grid(True, linestyle="--", alpha=0.7)

plt.subplot(1, 2, 2)
sns.violinplot(x="Reformulation", y="Rel_Gap", data=df, inner="quartile")
plt.title("Violin Plot: Relative Relaxation Gap by Reformulation")
plt.ylabel("Relative Relaxation Gap")
plt.xlabel("Reformulation Type")
plt.grid(True, linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()

# Option 2: Bar Charts of Average Gaps
print("\n2. Bar Chart of Average Gaps")
plt.figure(figsize=(8, 6))
sns.barplot(x="Reformulation", y="Rel_Gap", data=df, estimator=np.mean, errorbar="sd", capsize=0.1)
plt.title("Average Relative Relaxation Gap by Reformulation (with StdDev)")
plt.ylabel("Average Relative Relaxation Gap")
plt.xlabel("Reformulation Type")
plt.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.show()

# Option 3: Scatter Plots for Pairwise Comparison
print("\n3. Scatter Plot for Pairwise Comparison (BigM vs Hull)")
# Pivot data to get reformulations as columns
df_pivot_gaps = df.pivot(index="Problem_Instance", columns="Reformulation", values="Rel_Gap")
df_pivot_gaps = (
    df_pivot_gaps.dropna()
)  # Ensure instances have data for both selected reformulations

if "BigM" in df_pivot_gaps.columns and "Hull" in df_pivot_gaps.columns:
    plt.figure(figsize=(7, 7))
    plt.scatter(df_pivot_gaps["BigM"], df_pivot_gaps["Hull"], alpha=0.7, edgecolors="k")

    # Add y=x line
    min_val = min(df_pivot_gaps["BigM"].min(), df_pivot_gaps["Hull"].min())
    max_val = max(df_pivot_gaps["BigM"].max(), df_pivot_gaps["Hull"].max())
    if pd.notna(min_val) and pd.notna(max_val):  # Check if min/max are not NaN
        plt.plot([min_val, max_val], [min_val, max_val], "r--", label="y=x (Equal Gaps)")
    else:
        print("Warning: Could not draw y=x line due to NaN values in min/max gap.")

    plt.xlabel("Relative Gap (BigM)")
    plt.ylabel("Relative Gap (Hull)")
    plt.title("Pairwise Comparison: BigM vs. Hull Relative Gaps")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.axis("equal")  # Ensure aspect ratio is equal for fair comparison
    plt.show()
else:
    print("BigM or Hull column missing in pivoted data for scatter plot.")


# Option 4: Paired Bar Charts or Dot Plots (for differences)
print("\n4. Bar Chart of Gap Differences (Hull - BigM)")
if "BigM" in df_pivot_gaps.columns and "Hull" in df_pivot_gaps.columns:
    df_pivot_gaps["Gap_Difference (Hull-BigM)"] = df_pivot_gaps["Hull"] - df_pivot_gaps["BigM"]
    # Sort for better visualization
    df_pivot_sorted_diff = df_pivot_gaps.sort_values("Gap_Difference (Hull-BigM)")

    plt.figure(figsize=(12, 7))
    colors = [
        "green" if x < 0 else "red" for x in df_pivot_sorted_diff["Gap_Difference (Hull-BigM)"]
    ]
    plt.bar(
        df_pivot_sorted_diff.index, df_pivot_sorted_diff["Gap_Difference (Hull-BigM)"], color=colors
    )
    plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
    plt.xlabel("Problem Instance")
    plt.ylabel("Relative Gap Difference (Hull_Gap - BigM_Gap)")
    plt.title("Difference in Relative Gaps (Negative means Hull is better)")
    plt.xticks(rotation=90, ha="center")
    plt.tight_layout()  # Adjust layout to make room for tick labels
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.show()
else:
    print("BigM or Hull column missing in pivoted data for difference plot.")


# Option 5: Performance Profiles
print("\n5. Performance Profiles for Relative Gaps")
# Use the df_pivot_gaps which has Problem_Instance as index,
# Reformulations as columns, Rel_Gap as values
# Make sure to include all reformulations you want to compare
df_perf = df.pivot(index="Problem_Instance", columns="Reformulation", values="Rel_Gap")
df_perf = df_perf.dropna()  # Only use instances where all reformulations have a gap

if not df_perf.empty:
    # 1. Find min_gap_p for each problem (row-wise min)
    df_perf["min_gap"] = df_perf[reformulations].min(axis=1)

    # 2. Calculate ratios: gap_rp / min_gap_p
    ratio_cols = []
    for reform_type in reformulations:
        if reform_type in df_perf.columns:
            col_name = f"ratio_{reform_type}"
            # Handle cases where min_gap is zero (or very small)
            # If min_gap is 0, and reform_type_gap is also 0, ratio is 1.
            # If min_gap is 0, and reform_type_gap > 0, ratio is effectively infinity.
            df_perf[col_name] = np.where(
                df_perf["min_gap"] < 1e-9,  # if min_gap is essentially zero
                np.where(
                    df_perf[reform_type] < 1e-9, 1.0, np.inf
                ),  # if reform_gap is also zero, ratio 1, else inf
                df_perf[reform_type] / df_perf["min_gap"],
            )
            ratio_cols.append(col_name)

    # 3. Define tau values (performance ratios)
    # We can define a fixed set or derive from data. For gaps, usually starts at 1.
    max_ratio = df_perf[ratio_cols].replace(np.inf, np.nan).max().max()  # Max finite ratio
    if pd.isna(max_ratio) or max_ratio < 2:
        max_ratio = 10  # Default if no large ratios
    taus = np.unique(
        np.concatenate(([1], np.geomspace(1.001, max(2, max_ratio), 50), [max_ratio * 1.1]))
    )
    taus = np.sort(taus)

    plt.figure(figsize=(10, 7))
    num_problems = len(df_perf)

    for reform_type in reformulations:
        if f"ratio_{reform_type}" in df_perf.columns:
            ratio_col_name = f"ratio_{reform_type}"
            fractions = [(df_perf[ratio_col_name] <= tau).sum() / num_problems for tau in taus]
            plt.plot(taus, fractions, label=reform_type, marker=".", markersize=4, linestyle="-")

    plt.xlabel("Performance Ratio (τ)")
    plt.ylabel(f"P(gap ≤ τ * best_gap) [Fraction of {num_problems} Problems]")
    plt.title("Performance Profile for Relative Relaxation Gaps")
    plt.legend(title="Reformulation")
    plt.xscale("log")  # Tau is often plotted on a log scale
    plt.grid(True, which="both", ls="--", alpha=0.7)
    plt.ylim([0, 1.05])
    plt.xlim(left=1)  # Start tau at 1
    plt.tight_layout()
    plt.show()
else:
    print("Pivoted data for performance profiles is empty. Check input data.")


# Option 6: Heatmaps
print("\n6. Heatmap of Relative Gaps")
# Using df_pivot_gaps from earlier, or re-pivot if necessary
df_heatmap_data = df.pivot(index="Problem_Instance", columns="Reformulation", values="Rel_Gap")
# For heatmap, NaN values can be problematic or can be visualized.
# Let's fill with a placeholder if needed,
# or ensure data is complete. For now, Seaborn handles NaNs by not coloring those cells.

if not df_heatmap_data.empty:
    plt.figure(figsize=(8, 10))
    sns.heatmap(
        df_heatmap_data[reformulations], annot=True, fmt=".2f", cmap="viridis_r", linewidths=0.5
    )
    # cmap="viridis_r" -> _r reverses the colormap, so smaller (better) gaps get "better" colors
    plt.title("Heatmap of Relative Relaxation Gaps")
    plt.ylabel("Problem Instance")
    plt.xlabel("Reformulation Type")
    plt.tight_layout()
    plt.show()
else:
    print("Pivoted data for heatmap is empty.")

print("\n--- All visualizations complete ---")
