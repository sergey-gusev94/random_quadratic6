"""
Analyze and visualize disjunctive feasible regions, 
tracking which disjuncts are feasible.

This module extends the functionality in plot_2d.py to track detailed feasibility information
across disjuncts and disjunctions, and visualize the different feasible regions 
with distinct colors.
"""

import importlib.util
import os
import pickle
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Import local modules
from matplotlib.colors import ListedColormap

# Get the path to the plot_2d.py file
current_dir = os.path.dirname(os.path.abspath(__file__))
plots_file_path = os.path.join(current_dir, "plot_2d.py")

# Import the module using its file path
spec = importlib.util.spec_from_file_location("plots_module", plots_file_path)
if spec is None:
    raise ImportError(f"Could not find module at {plots_file_path}")
plots_module = importlib.util.module_from_spec(spec)
sys.modules["plots_module"] = plots_module
if spec.loader is None:
    raise ImportError(f"No loader found for module at {plots_file_path}")
spec.loader.exec_module(plots_module)

# Now access the functions we need
calculate_contour_levels = plots_module.calculate_contour_levels
evaluate_constraint = plots_module.evaluate_constraint
evaluate_objective = plots_module.evaluate_objective
extract_disjunctive_constraints = plots_module.extract_disjunctive_constraints
get_solution_points = plots_module.get_solution_points
verify_model = plots_module.verify_model


def encode_feasible_combination(disjunction_feasibility: Dict[int, Set[int]]) -> str:
    """
    Encode a feasible combination of disjuncts into a string for unique identification.

    Parameters
    ----------
    disjunction_feasibility : Dict[int, Set[int]]
        Dictionary mapping disjunction indices to sets of feasible disjunct indices

    Returns
    -------
    str
        Encoded string representation of the feasible combination
    """
    # Sort by disjunction index for consistency
    encoded_parts = []
    for disjunction in sorted(disjunction_feasibility.keys()):
        # Convert set to sorted list for consistent encoding
        disjuncts = sorted(disjunction_feasibility[disjunction])
        encoded_parts.append(f"D{disjunction}:[{','.join(map(str, disjuncts))}]")

    return "|".join(encoded_parts)


def save_disjunct_feasibility_results(
    model_name: str,
    X1: np.ndarray,
    X2: np.ndarray,
    Z_obj: np.ndarray,
    feasibility_map: np.ndarray,
    region_combinations: Dict[int, Dict[int, Set[int]]],
    region_codes: Dict[int, str],
    solution_points: Dict[str, Tuple[float, float]],
    min_x1: float,
    max_x1: float,
    min_x2: float,
    max_x2: float,
    levels: Any,
) -> str:
    """
    Save disjunct feasibility results to a file for later plotting without recalculation.

    Parameters
    ----------
    model_name : str
        Name of the model
    X1 : np.ndarray
        X1 grid coordinates
    X2 : np.ndarray
        X2 grid coordinates
    Z_obj : np.ndarray
        Objective function values at grid points
    feasibility_map : np.ndarray
        Integer array indicating the region ID for each point
    region_combinations : Dict[int, Dict[int, Set[int]]]
        Dictionary mapping region IDs to disjunct combinations
    region_codes : Dict[int, str]
        Dictionary mapping region IDs to encoded string representations
    solution_points : Dict[str, Tuple[float, float]]
        Dictionary of solution points by strategy
    min_x1, max_x1, min_x2, max_x2 : float
        Plot bounds
    levels : Any
        Contour levels

    Returns
    -------
    str
        Path to the saved data file
    """
    data_dir = os.path.join(os.path.dirname(os.getcwd()), "data")
    cache_dir = os.path.join(data_dir, "disjunct_combination_cache")
    os.makedirs(cache_dir, exist_ok=True)

    # Create a dictionary with all data
    data = {
        "model_name": model_name,
        "X1": X1,
        "X2": X2,
        "Z_obj": Z_obj,
        "feasibility_map": feasibility_map,
        "region_combinations": region_combinations,
        "region_codes": region_codes,
        "solution_points": solution_points,
        "min_x1": min_x1,
        "max_x1": max_x1,
        "min_x2": min_x2,
        "max_x2": max_x2,
        "levels": levels,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Save to file
    file_path = os.path.join(cache_dir, f"{model_name.replace('.pkl', '')}_disjunct_data.pkl")
    with open(file_path, "wb") as f:
        pickle.dump(data, f)

    print(f"Disjunct feasibility results saved to: {file_path}")
    return file_path


def load_disjunct_feasibility_results(model_name: str) -> Dict[str, Any]:
    """
    Load previously saved disjunct feasibility results.

    Parameters
    ----------
    model_name : str
        Name of the model

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all saved feasibility data
    """
    data_dir = os.path.join(os.path.dirname(os.getcwd()), "data")
    cache_dir = os.path.join(data_dir, "disjunct_combination_cache")
    file_path = os.path.join(cache_dir, f"{model_name.replace('.pkl', '')}_disjunct_data.pkl")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cached disjunct feasibility data not found: {file_path}")

    # Load data
    with open(file_path, "rb") as f:
        data = pickle.load(f)

    print(f"Loaded disjunct feasibility results from: {file_path}")
    print(f"Original calculation timestamp: {data['timestamp']}")

    # Ensure we're returning a properly typed dictionary
    result: Dict[str, Any] = data
    return result


def check_for_cached_disjunct_results(model_name: str) -> bool:
    """
    Check if cached disjunct feasibility results exist for this model.

    Parameters
    ----------
    model_name : str
        Name of the model

    Returns
    -------
    bool
        True if cached data exists, False otherwise
    """
    data_dir = os.path.join(os.path.dirname(os.getcwd()), "data")
    cache_dir = os.path.join(data_dir, "disjunct_combination_cache")
    file_path = os.path.join(cache_dir, f"{model_name.replace('.pkl', '')}_disjunct_data.pkl")

    return os.path.exists(file_path)


def generate_distinct_colors(n: int) -> List[Tuple[float, float, float, float]]:
    """
    Generate a list of visually distinct colors for plotting different regions.

    Parameters
    ----------
    n : int
        Number of distinct colors needed

    Returns
    -------
    List[Tuple[float, float, float, float]]
        List of RGBA colors
    """
    # Base colormap options depending on number of regions
    if n <= 10:
        # For small number of regions, use qualitative colormap
        cmap = plt.cm.get_cmap("tab10", n)
    elif n <= 20:
        # For more regions, use a different qualitative map
        cmap = plt.cm.get_cmap("tab20", n)
    else:
        # For many regions, use a spectral map
        cmap = plt.cm.get_cmap("gist_rainbow", n)

    # Generate colors with alpha
    colors: List[Tuple[float, float, float, float]] = [(*cmap(i)[:3], 0.95) for i in range(n)]

    return colors


def plot_disjunct_regions(
    model_name: str,
    X1: np.ndarray,
    X2: np.ndarray,
    Z_obj: np.ndarray,
    feasibility_map: np.ndarray,
    region_combinations: Dict[int, Dict[int, Set[int]]],
    region_codes: Dict[int, str],
    solution_points: Dict[str, Tuple[float, float]],
    min_x1: float,
    max_x1: float,
    min_x2: float,
    max_x2: float,
    levels: np.ndarray,
) -> str:
    """
    Create and save a plot showing different feasible regions with distinct colors.

    Parameters
    ----------
    model_name : str
        Name of the model
    X1 : np.ndarray
        X1 grid coordinates
    X2 : np.ndarray
        X2 grid coordinates
    Z_obj : np.ndarray
        Objective function values at grid points
    feasibility_map : np.ndarray
        Integer array indicating the region ID for each point
    region_combinations : Dict[int, Dict[int, Set[int]]]
        Dictionary mapping region IDs to disjunct combinations
    region_codes : Dict[int, str]
        Dictionary mapping region IDs to encoded string representations
    solution_points : Dict[str, Tuple[float, float]]
        Dictionary of solution points by strategy
    min_x1, max_x1, min_x2, max_x2 : float
        Plot bounds
    levels : np.ndarray
        Contour levels

    Returns
    -------
    str
        Path to the saved plot file
    """
    # Create figure with increased size to accommodate external legend
    plt.figure(figsize=(14, 14))

    # Generate distinct colors for each region
    num_regions = len(region_combinations)
    region_colors = generate_distinct_colors(num_regions + 1)  # +1 for infeasible region

    # Create a visualization of the feasible regions
    # First, create a color map where 0 is white (infeasible) and each region has a distinct color
    colors: List[Tuple[float, float, float, float]] = [
        (1, 1, 1, 0)
    ]  # Start with transparent white for infeasible region (0)
    for i in range(1, num_regions + 1):
        colors.append(region_colors[i])

    # Create a custom colormap
    region_cmap = ListedColormap(colors)

    # Plot regions
    plt.imshow(
        feasibility_map,
        extent=[min_x1, max_x1, min_x2, max_x2],
        origin="lower",
        cmap=region_cmap,
        alpha=1,
    )

    # Add contour lines for the objective function
    contour = plt.contour(
        X1,
        X2,
        Z_obj,
        levels=levels,
        colors="black",
        linewidths=0.8,
    )

    # Add contour labels
    plt.clabel(contour, inline=True, fontsize=9, fmt="%.2e")

    # Plot solution points
    solution_markers = {
        "gdp.bigm": "o",
        "gdp.hull": "s",
        "gdp.hull_exact": "^",
        "gdp.hull_reduced_y": "x",
        "baron_gdp.bigm": "o",
        "baron_gdp.hull": "s",
        "baron_gdp.hull_exact": "^",
        "baron_gdp.hull_reduced_y": "x",
    }
    solution_colors = {
        "gdp.bigm": "red",
        "gdp.hull": "blue",
        "gdp.hull_exact": "purple",
        "gdp.hull_reduced_y": "orange",
        "baron_gdp.bigm": "darkred",
        "baron_gdp.hull": "darkblue",
        "baron_gdp.hull_exact": "indigo",
        "baron_gdp.hull_reduced_y": "darkorange",
    }

    # Print solution points
    print("\nSolution points found for strategies:")
    for strategy, point in solution_points.items():
        print(f"Strategy: {strategy}, Point: ({point[0]:.6f}, {point[1]:.6f})")

        # Find which region contains this solution point
        x1_idx = int((point[0] - min_x1) / (max_x1 - min_x1) * (X1.shape[1] - 1))
        x2_idx = int((point[1] - min_x2) / (max_x2 - min_x2) * (X1.shape[0] - 1))

        # Check bounds
        if 0 <= x1_idx < X1.shape[1] and 0 <= x2_idx < X1.shape[0]:
            region_id = feasibility_map[x2_idx, x1_idx]
            if region_id > 0:
                region_code = region_codes[region_id]
                print(f"  Located in region {region_id}: {region_code}")
            else:
                print("  Not in any feasible region (possibly on boundary)")
        else:
            print("  Out of bounds of the analyzed grid")

    # Plot solution points
    for strategy, point in solution_points.items():
        marker = solution_markers.get(strategy, "*")
        color = solution_colors.get(strategy, "black")
        plt.plot(
            point[0],
            point[1],
            marker=marker,
            color=color,
            markersize=15,
            markeredgecolor="black",
            markeredgewidth=1.5,
            label=f"{strategy}: ({point[0]:.4f}, {point[1]:.4f})",
        )

    # Add title and labels
    plt.title(f"Disjunctive Feasible Regions ({num_regions} regions found)", fontsize=14)
    plt.xlabel("x1", fontsize=12)
    plt.ylabel("x2", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xlim(min_x1, max_x1)
    plt.ylim(min_x2, max_x2)

    # Create a custom legend for the regions
    region_patches = []
    for region_id, region_code in region_codes.items():
        color = region_colors[region_id]
        patch = plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=0.7, edgecolor="black")
        region_patches.append((patch, f"Region {region_id}: {region_code}"))

    # Add solution points to legend handles and labels
    solution_handles, solution_labels = plt.gca().get_legend_handles_labels()
    all_handles = [patch for patch, _ in region_patches] + solution_handles
    all_labels = [label for _, label in region_patches] + solution_labels

    # Adjust layout for main plot before adding legend
    plt.tight_layout()

    # Create a separate figure just for the legend
    legend_fig = plt.figure(figsize=(14, num_regions // 3 + 5))  # Size based on number of regions
    legend_ax = legend_fig.add_subplot(111)
    legend_ax.axis("off")  # Hide axes

    # Add the legend to the new figure
    legend_ax.legend(
        all_handles,
        all_labels,
        loc="center",
        fontsize=9,
        ncol=3,  # Use multiple columns
        frameon=True,
        fancybox=True,
        shadow=True,
        title="Feasible Regions and Solution Points",
    )

    # Adjust legend figure layout
    legend_fig.tight_layout()

    # Save main figure
    data_dir = os.path.join(os.path.dirname(os.getcwd()), "data")
    plots_dir = os.path.join(data_dir, "disjunct_plots")
    os.makedirs(plots_dir, exist_ok=True)

    base_filename = model_name.replace(".pkl", "")
    output_path = os.path.join(plots_dir, f"{base_filename}_disjunct_regions.png")

    # Create unique filename if needed
    counter = 1
    while os.path.exists(output_path):
        output_path = os.path.join(plots_dir, f"{base_filename}_disjunct_regions_{counter}.png")
        counter += 1

    plt.figure(1)  # Switch back to main figure
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Disjunct regions plot saved to: {output_path}")

    # Save legend figure
    legend_path = os.path.join(plots_dir, f"{base_filename}_legend.png")
    counter = 1
    while os.path.exists(legend_path):
        legend_path = os.path.join(plots_dir, f"{base_filename}_legend_{counter}.png")
        counter += 1

    plt.figure(2)  # Switch to legend figure
    plt.savefig(legend_path, dpi=300, bbox_inches="tight")
    print(f"Legend saved to: {legend_path}")

    return output_path


def analyze_disjunct_feasibility(
    model: Any,
    constraints: List[Dict[str, Any]],
    solution_points: Dict[str, Tuple[float, float]],
    grid_size: int = 1000,
    save_calculations: bool = True,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze the feasibility of different disjunct combinations across the domain.

    Parameters
    ----------
    model : Any
        The Pyomo model
    constraints : List[Dict[str, Any]]
        List of constraint data
    solution_points : Dict[str, Tuple[float, float]]
        Dictionary mapping strategy names to solution points
    grid_size : int
        Size of the grid for plotting
    save_calculations : bool
        Whether to save calculation results to a file
    model_name : Optional[str]
        Name of the model file for saving results

    Returns
    -------
    Dict[str, Any]
        Dictionary with all calculation results for potential saving
    """
    # Use fixed range from -1 to 1 for both axes
    min_x1, max_x1 = -1.0, 1.0
    min_x2, max_x2 = -1.0, 1.0

    # Create grid for plotting
    x1_grid = np.linspace(min_x1, max_x1, grid_size)
    x2_grid = np.linspace(min_x2, max_x2, grid_size)
    X1, X2 = np.meshgrid(x1_grid, x2_grid)

    # Evaluate objective function on the grid
    print(f"\nEvaluating objective function on {grid_size}x{grid_size} grid...")
    Z_obj = np.zeros_like(X1)
    for i in range(grid_size):
        for j in range(grid_size):
            Z_obj[i, j] = evaluate_objective(model, X1[i, j], X2[i, j])

    # Get disjunctions and disjuncts from model
    disjunctions = list(model.disjunctions)
    disjuncts = list(model.disjuncts)

    print(
        f"Model has {len(disjunctions)} disjunctions and "
        f"{len(disjuncts)} disjuncts per disjunction"
    )

    # Initialize a data structure to store which disjuncts are feasible for each point
    # For each grid point, we'll store a dictionary,
    # mapping disjunction indices to sets of feasible disjunct indices
    point_feasibility = np.empty((grid_size, grid_size), dtype=object)

    # Initialize the array with empty dictionaries
    for i in range(grid_size):
        for j in range(grid_size):
            point_feasibility[i, j] = {}

    # Create a mask for tracking which points are still potentially feasible
    # (i.e., they haven't been proven infeasible in any disjunction yet)
    still_feasible = np.ones((grid_size, grid_size), dtype=bool)

    # Track progress
    total_evaluations = grid_size * grid_size * len(disjunctions) * len(disjuncts)
    total_points = grid_size * grid_size
    evaluation_count = 0
    early_termination_count = 0
    points_determined_infeasible = 0

    # Report progress at regular intervals
    report_interval = 1000000  # Report every million evaluations
    next_report = report_interval

    # Track the start time to estimate remaining time
    start_time = pd.Timestamp.now()
    last_report_time = start_time

    # Evaluate constraints for each disjunct
    print(f"\nEvaluating constraints for all disjuncts on {grid_size}x{grid_size} grid...")

    # For each disjunction
    for d_idx, disjunction in enumerate(disjunctions):
        print(f"Processing disjunction {d_idx+1}/{len(disjunctions)}")

        # For each grid point that is still potentially feasible
        for i in range(grid_size):
            for j in range(grid_size):
                # Skip points that are already known to be infeasible
                if not still_feasible[i, j]:
                    early_termination_count += len(disjuncts)  # Count skipped evaluations
                    continue

                # For each disjunct in this disjunction, check if it's feasible
                feasible_disjuncts = set()

                for k_idx, disjunct in enumerate(disjuncts):
                    # Get constraints for this disjunct
                    disjunct_constraints = [
                        c
                        for c in constraints
                        if c["disjunction"] == disjunction and c["disjunct"] == disjunct
                    ]

                    # Assume disjunct is feasible until proven otherwise
                    is_feasible = True

                    # Check all constraints for this disjunct
                    for constraint in disjunct_constraints:
                        # Evaluate constraint: x^T Q x + c^T x + d <= 0
                        constraint_value = evaluate_constraint(
                            constraint["Q"], constraint["c"], constraint["d"], X1[i, j], X2[i, j]
                        )

                        # Count evaluation
                        evaluation_count += 1

                        # Check if constraint is violated
                        if constraint_value > 0:
                            is_feasible = False
                            break

                    # If disjunct is feasible, add it to the set of feasible disjuncts for the point
                    if is_feasible:
                        feasible_disjuncts.add(k_idx)

                # Store the set of feasible disjuncts for this disjunction at this point
                if feasible_disjuncts:  # Only store if there are feasible disjuncts
                    point_feasibility[i, j][d_idx] = feasible_disjuncts
                else:
                    # If no disjuncts are feasible for this disjunction, the point is infeasible
                    # Mark it as infeasible to skip in future disjunctions
                    still_feasible[i, j] = False
                    points_determined_infeasible += 1

                # Report progress
                if evaluation_count >= next_report:
                    progress = evaluation_count / total_evaluations * 100
                    print(
                        f"  Progress: {evaluation_count:,}/{total_evaluations:,} "
                        f"evaluations ({progress:.1f}%)"
                    )
                    print(f"  Early terminations: {early_termination_count:,} evaluations skipped")
                    next_report = evaluation_count + report_interval

                # Calculate elapsed time and estimate remaining time
                if evaluation_count >= next_report:
                    current_time = pd.Timestamp.now()
                    total_elapsed = (current_time - start_time).total_seconds()
                    print(f"  Total elapsed time: {total_elapsed:.1f} seconds")
                    elapsed_since_last = (current_time - last_report_time).total_seconds()
                    last_report_time = current_time

                    # Calculate evaluations per second
                    evals_per_second = (
                        report_interval / elapsed_since_last if elapsed_since_last > 0 else 0
                    )

                    # Estimate remaining time
                    remaining_evals = total_evaluations - evaluation_count - early_termination_count
                    remaining_seconds = (
                        remaining_evals / evals_per_second if evals_per_second > 0 else 0
                    )

                    # Format as hours:minutes:seconds
                    remaining_time_str = str(pd.Timedelta(seconds=int(remaining_seconds)))

                    # Overall progress
                    progress = evaluation_count / total_evaluations * 100
                    print(f"\nProgress Report at {current_time.strftime('%H:%M:%S')}:")
                    print(
                        f"  Evaluations: {evaluation_count:,}/{total_evaluations:,} "
                        f"evaluations ({progress:.1f}%)"
                    )
                    print(f"  Early terminations: {early_termination_count:,} evaluations skipped")
                    print(
                        f"  Grid points processed: Processing disjunction "
                        f"{d_idx+1}/{len(disjunctions)}"
                    )
                    print(
                        f"  Points determined infeasible: "
                        f"{points_determined_infeasible:,}/{total_points:,} "
                        f"({points_determined_infeasible/total_points*100:.1f}%)"
                    )
                    print(f"  Performance: {evals_per_second:.1f} evaluations/second")
                    print(f"  Estimated remaining time: {remaining_time_str}")

                    next_report = evaluation_count + report_interval

    print(f"Completed {evaluation_count:,} constraint evaluations")
    print(f"Skipped {early_termination_count:,} evaluations due to early termination")
    print(
        f"Total efficiency: {(evaluation_count + early_termination_count) / total_evaluations:.2%}"
    )

    # Calculate total execution time
    total_time = (pd.Timestamp.now() - start_time).total_seconds()
    hours, remainder = divmod(total_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Print final statistics
    print("\nExecution Summary:")
    print(f"  Total execution time: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    print(
        f"  Total evaluations: {evaluation_count:,} completed, "
        f"{early_termination_count:,} skipped"
    )
    print(
        f"  Points determined infeasible: "
        f"{points_determined_infeasible:,}/{total_points:,} "
        f"({points_determined_infeasible/total_points*100:.1f}%)"
    )
    print(
        f"  Average performance: "
        f"{(evaluation_count + early_termination_count) / total_time:.1f} evaluations/second"
    )
    print(
        f"  Total efficiency: "
        f"{(evaluation_count + early_termination_count) / total_evaluations:.2%} "
        f"of theoretical maximum evaluations"
    )

    # Determine which points are feasible overall (have feasible disjuncts for all disjunctions)
    overall_feasibility = np.zeros((grid_size, grid_size), dtype=bool)

    for i in range(grid_size):
        for j in range(grid_size):
            # Check if this point has feasible disjuncts for all disjunctions
            if len(point_feasibility[i, j]) == len(disjunctions):
                overall_feasibility[i, j] = True

    # Verify that our still_feasible mask is consistent with the explicit check
    if not np.array_equal(still_feasible, overall_feasibility):
        print(
            """Warning: Inconsistency detected between early termination tracking and 
            final feasibility check"""
        )
        # Use the more conservative result (explicit check)
        # This shouldn't happen, but better safe than sorry

    # Count how many points are feasible
    num_feasible_points = np.sum(overall_feasibility)
    print(
        f"Found {num_feasible_points} feasible points out of {grid_size * grid_size} "
        f"({num_feasible_points/(grid_size * grid_size)*100:.2f}%)"
    )

    # Identify distinct feasible regions (combinations of disjuncts)
    print("\nIdentifying distinct feasible regions...")

    # Map from encoded disjunct combination to region ID
    combination_to_region = {}

    # Map from region ID to disjunct combination
    region_combinations = {}

    # Map from region ID to encoded string representation
    region_codes = {}

    # Create a map of region IDs for visualization
    feasibility_map = np.zeros((grid_size, grid_size), dtype=int)

    # Assign region IDs to points
    region_id = 1  # Start from 1; 0 represents infeasible regions

    for i in range(grid_size):
        for j in range(grid_size):
            if overall_feasibility[i, j]:
                # Encode this point's disjunct combination
                encoded = encode_feasible_combination(point_feasibility[i, j])

                # Check if we've seen this combination before
                if encoded not in combination_to_region:
                    # New region found
                    combination_to_region[encoded] = region_id
                    region_combinations[region_id] = point_feasibility[i, j].copy()
                    region_codes[region_id] = encoded
                    region_id += 1

                # Assign region ID to this point
                feasibility_map[i, j] = combination_to_region[encoded]

    # Report the number of distinct regions found
    num_regions = region_id - 1
    print(f"Found {num_regions} distinct feasible regions")

    # Print information about each region
    for region_id, combination in region_combinations.items():
        print(f"\nRegion {region_id}: {region_codes[region_id]}")

        # Count points in this region
        points_in_region = np.sum(feasibility_map == region_id)
        percent_of_feasible = points_in_region / num_feasible_points * 100
        percent_of_total = points_in_region / (grid_size * grid_size) * 100

        print(
            f"  Points: {points_in_region} "
            f"({percent_of_feasible:.2f}% of feasible, {percent_of_total:.2f}% of total)"
        )

        # Print disjunct information
        for disjunction, disjuncts in combination.items():
            print(f"  Disjunction {disjunction}: Disjuncts {sorted(disjuncts)}")

    # Find the min and max values in Z_obj for contour levels
    z_min, z_max = np.min(Z_obj), np.max(Z_obj)
    print(f"\nObjective function range: {z_min} to {z_max}")

    # Calculate contour levels
    levels = calculate_contour_levels(z_min, z_max)

    # Use model_name or a default if None is provided
    if model_name is None:
        model_name = "unnamed_model.pkl"

    # Plot the results
    plot_disjunct_regions(
        model_name,
        X1,
        X2,
        Z_obj,
        feasibility_map,
        region_combinations,
        region_codes,
        solution_points,
        min_x1,
        max_x1,
        min_x2,
        max_x2,
        levels,
    )

    # Create results dictionary
    calculation_data = {
        "model_name": model_name,
        "X1": X1,
        "X2": X2,
        "Z_obj": Z_obj,
        "feasibility_map": feasibility_map,
        "region_combinations": region_combinations,
        "region_codes": region_codes,
        "solution_points": solution_points,
        "min_x1": min_x1,
        "max_x1": max_x1,
        "min_x2": min_x2,
        "max_x2": max_x2,
        "levels": levels,
    }

    # Save calculation results if requested
    if save_calculations:
        save_disjunct_feasibility_results(
            model_name,
            X1,
            X2,
            Z_obj,
            feasibility_map,
            region_combinations,
            region_codes,
            solution_points,
            min_x1,
            max_x1,
            min_x2,
            max_x2,
            levels,
        )

    return calculation_data


def plot_from_cached_results(data: Dict[str, Any]) -> None:
    """
    Plot disjunct regions using pre-calculated data, but always load fresh solution points.

    Parameters
    ----------
    data : Dict[str, Any]
        Dictionary containing all calculation data
    """
    # Extract data
    model_name = data["model_name"]
    X1 = data["X1"]
    X2 = data["X2"]
    Z_obj = data["Z_obj"]
    feasibility_map = data["feasibility_map"]
    region_combinations = data["region_combinations"]
    region_codes = data["region_codes"]
    min_x1 = data["min_x1"]
    max_x1 = data["max_x1"]
    min_x2 = data["min_x2"]
    max_x2 = data["max_x2"]
    levels = data["levels"]

    # Always load fresh solution points from Excel
    solution_points = get_solution_points(model_name)

    # Plot the results
    plot_disjunct_regions(
        model_name,
        X1,
        X2,
        Z_obj,
        feasibility_map,
        region_combinations,
        region_codes,
        solution_points,
        min_x1,
        max_x1,
        min_x2,
        max_x2,
        levels,
    )


def main(model_name: str, use_cache: bool = True, save_cache: bool = True) -> None:
    """
    Main function to analyze and visualize disjunctive feasible regions for a 2D model.

    Parameters
    ----------
    model_name : str
        Name of the model file
    use_cache : bool
        Whether to use cached calculation results if available
    save_cache : bool
        Whether to save calculation results for future use
    """
    # Check if we can use cached results
    if use_cache and check_for_cached_disjunct_results(model_name):
        print(f"Found cached disjunct feasibility results for {model_name}")
        data = load_disjunct_feasibility_results(model_name)
        plot_from_cached_results(data)
        return

    # No cache or not using cache, do full calculation
    print(
        f"No cached data found or not using cache. "
        f"Running full disjunct feasibility analysis for {model_name}"
    )

    # Verify and load model
    model = verify_model(model_name)

    # Get solution points from Excel results
    solution_points = get_solution_points(model_name)

    # Extract disjunctive constraints
    constraints = extract_disjunctive_constraints(model)

    # Analyze disjunct feasibility and create visualization
    analyze_disjunct_feasibility(
        model, constraints, solution_points, save_calculations=save_cache, model_name=model_name
    )

    print(f"Disjunct feasibility analysis completed for model: {model_name}")


if __name__ == "__main__":
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze and visualize disjunctive feasible regions"
    )
    parser.add_argument(
        "model_name",
        nargs="?",
        default="model_no_mode_2025-05-01_13-48-10_dim2_disj2_disjper2_constper2_feas2_1.pkl",
        help="Name of the model file",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable use of cached calculations"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Disable saving calculations to cache"
    )
    parser.add_argument(
        "--grid-size", type=int, default=500, help="Grid size for the analysis (default: 500)"
    )

    args = parser.parse_args()

    # Run main function with provided arguments
    main(model_name=args.model_name, use_cache=not args.no_cache, save_cache=not args.no_save)
