#!/usr/bin/env python3
"""
Aggregate Solution Outcomes Script

This script searches through all folders in the archive directory, finds all
solution_outcomes.txt files, and aggregates them into a single comprehensive report.

The script will:
1. Find all solution_outcomes.txt files in the archive directory
2. Parse each file to extract solver performance data
3. Create a comprehensive aggregated report
4. Save the aggregated report in the archive folder

Author: Generated for random_quadratic research project
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast


def find_solution_outcome_files(archive_dir: str) -> List[str]:
    """
    Find all solution_outcomes.txt files in the archive directory.

    Parameters
    ----------
    archive_dir : str
        Path to the archive directory

    Returns
    -------
    List[str]
        List of paths to solution_outcomes.txt files
    """
    outcome_files = []

    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file == "solution_outcomes.txt":
                outcome_files.append(os.path.join(root, file))

    return outcome_files


def extract_experiment_info(file_path: str) -> Dict[str, str]:
    """
    Extract experiment information from the file path.

    Parameters
    ----------
    file_path : str
        Path to the solution_outcomes.txt file

    Returns
    -------
    Dict[str, str]
        Dictionary containing experiment metadata
    """
    # Extract information from path like:
    # /archive/non-conv_baron/plots/gams_baron/solution_outcomes.txt
    path_parts = Path(file_path).parts

    # Find archive index
    archive_idx = None
    for i, part in enumerate(path_parts):
        if part == "archive":
            archive_idx = i
            break

    if archive_idx is None or archive_idx + 1 >= len(path_parts):
        return {"experiment": "unknown", "solver_combo": "unknown"}

    experiment = path_parts[archive_idx + 1]  # e.g., "non-conv_baron"

    # Extract solver combination from the path
    solver_combo = "unknown"
    for part in path_parts[archive_idx + 2 :]:
        if "gams_" in part:
            solver_combo = part
            break

    return {"experiment": experiment, "solver_combo": solver_combo, "full_path": file_path}


def parse_solution_outcomes_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse a solution_outcomes.txt file and extract the data.

    Parameters
    ----------
    file_path : str
        Path to the solution_outcomes.txt file

    Returns
    -------
    Optional[Dict]
        Dictionary containing parsed data or None if parsing failed
    """
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Extract metadata
        time_limit_match = re.search(r"Time limit: (\d+) seconds", content)
        tolerance_match = re.search(r"Objective tolerance: ([\d.e-]+)", content)

        time_limit = int(time_limit_match.group(1)) if time_limit_match else None
        obj_tolerance = float(tolerance_match.group(1)) if tolerance_match else None

        # Extract strategy data
        strategy_data = []

        # Find the table section using more robust parsing
        lines = content.split("\n")
        in_table = False
        summary_started = False

        for line in lines:
            line = line.strip()

            # Skip until we find the table header
            if "Strategy" in line and "Optimal" in line and "Timeout" in line:
                in_table = True
                continue

            # Stop when we reach the summary section
            if "Summary Statistics:" in line:
                summary_started = True
                continue

            # Parse the TOTAL line from Summary Statistics
            if summary_started and "TOTAL" in line:
                # Use regex to extract numbers from the TOTAL line
                numbers = re.findall(r"\b\d+\b", line)
                if len(numbers) >= 7:
                    try:
                        total_data = {
                            "strategy": "TOTAL",
                            "optimal": int(numbers[0]),
                            "timeout": int(numbers[1]),
                            "infeasible": int(numbers[2]),
                            "wrong_optimal": int(numbers[3]),
                            "solver_error": int(numbers[4]),
                            "missing": int(numbers[5]),
                            "total": int(numbers[6]),
                        }
                        strategy_data.append(total_data)
                    except (ValueError, IndexError):
                        pass
                continue

            # Skip header separator lines
            if line.startswith("-") or line.startswith("="):
                continue

            # Parse strategy data lines
            if in_table and not summary_started and line and not line.startswith("TOTAL"):
                # Use regex to find all numbers in the line
                numbers = re.findall(r"\b\d+\b", line)

                # Extract strategy name (everything before the first number)
                strategy_match = re.match(r"^([^0-9]+)", line)
                if strategy_match and len(numbers) >= 7:
                    strategy_name = strategy_match.group(1).strip()

                    try:
                        strategy_info = {
                            "strategy": strategy_name,
                            "optimal": int(numbers[0]),
                            "timeout": int(numbers[1]),
                            "infeasible": int(numbers[2]),
                            "wrong_optimal": int(numbers[3]),
                            "solver_error": int(numbers[4]),
                            "missing": int(numbers[5]),
                            "total": int(numbers[6]),
                        }
                        strategy_data.append(strategy_info)
                    except (ValueError, IndexError):
                        # Skip lines that don't parse correctly
                        continue

        return {
            "time_limit": time_limit,
            "obj_tolerance": obj_tolerance,
            "strategies": strategy_data,
            "file_path": file_path,
        }

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None


def create_aggregated_report(parsed_data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Create a comprehensive aggregated report from all parsed data.

    Parameters
    ----------
    parsed_data : List[Dict]
        List of parsed data from all solution_outcomes.txt files
    output_file : str
        Path to save the aggregated report
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_file, "w") as f:
        f.write("AGGREGATED SOLUTION OUTCOMES REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Generated on: {current_time}\n")
        f.write(f"Total experiments analyzed: {len(parsed_data)}\n\n")

        # Write individual experiment summaries
        f.write("INDIVIDUAL EXPERIMENT SUMMARIES\n")
        f.write("=" * 80 + "\n\n")

        for i, data in enumerate(parsed_data, 1):
            exp_info = extract_experiment_info(data["file_path"])

            f.write(f"{i}. EXPERIMENT: {exp_info['experiment'].upper()}\n")
            f.write(f"   Solver: {exp_info['solver_combo']}\n")
            f.write(f"   Time limit: {data['time_limit']} seconds\n")
            f.write(f"   Objective tolerance: {data['obj_tolerance']}\n")
            f.write(f"   File: {data['file_path']}\n\n")

            # Write strategy table for this experiment
            f.write(
                f"   {'Strategy':<20} {'Optimal':<8} {'Timeout':<8} {'Infeasible':<10} "
                f"{'Wrong_Opt':<9} {'Solver_Err':<10} {'Missing':<8} {'Total':<8}\n"
            )
            f.write("   " + "-" * 85 + "\n")

            # Sort strategies to put TOTAL at the end
            strategies = [s for s in data["strategies"] if s["strategy"] != "TOTAL"]
            total_row = next((s for s in data["strategies"] if s["strategy"] == "TOTAL"), None)

            for strategy in strategies:
                f.write(
                    f"   {strategy['strategy']:<20} {strategy['optimal']:<8} "
                    f"{strategy['timeout']:<8} {strategy['infeasible']:<10} "
                    f"{strategy['wrong_optimal']:<9} {strategy['solver_error']:<10} "
                    f"{strategy['missing']:<8} {strategy['total']:<8}\n"
                )

            # Write totals for this experiment
            if total_row:
                f.write("   " + "-" * 85 + "\n")
                f.write(
                    f"   {'TOTAL':<20} {total_row['optimal']:<8} "
                    f"{total_row['timeout']:<8} {total_row['infeasible']:<10} "
                    f"{total_row['wrong_optimal']:<9} {total_row['solver_error']:<10} "
                    f"{total_row['missing']:<8} {total_row['total']:<8}\n"
                )

            f.write("\n" + "=" * 80 + "\n\n")

        # Create overall aggregated statistics
        f.write("OVERALL AGGREGATED STATISTICS\n")
        f.write("=" * 80 + "\n\n")

        # Aggregate by strategy across all experiments
        strategy_aggregates = {}
        experiment_totals = {}

        for data in parsed_data:
            exp_info = extract_experiment_info(data["file_path"])
            exp_key = f"{exp_info['experiment']}_{exp_info['solver_combo']}"

            for strategy in data["strategies"]:
                if strategy["strategy"] != "TOTAL":
                    strat_name = strategy["strategy"]
                    if strat_name not in strategy_aggregates:
                        strategy_aggregates[strat_name] = {
                            "optimal": 0,
                            "timeout": 0,
                            "infeasible": 0,
                            "wrong_optimal": 0,
                            "solver_error": 0,
                            "missing": 0,
                            "total": 0,
                            "experiments": [],
                        }

                    # Add to aggregate
                    for key in [
                        "optimal",
                        "timeout",
                        "infeasible",
                        "wrong_optimal",
                        "solver_error",
                        "missing",
                        "total",
                    ]:
                        if isinstance(strategy_aggregates[strat_name][key], int) and isinstance(
                            strategy[key], int
                        ):
                            strategy_aggregates[strat_name][key] += strategy[key]

                    experiments_list = cast(
                        List[str], strategy_aggregates[strat_name]["experiments"]
                    )
                    experiments_list.append(exp_key)

                # Track experiment totals
                if strategy["strategy"] == "TOTAL":
                    experiment_totals[exp_key] = strategy

        # Write strategy aggregates
        f.write("STRATEGY PERFORMANCE ACROSS ALL EXPERIMENTS\n")
        f.write("-" * 80 + "\n\n")

        f.write(
            f"{'Strategy':<20} {'Optimal':<8} {'Timeout':<8} {'Infeasible':<10} "
            f"{'Wrong_Opt':<9} {'Solver_Err':<10} {'Missing':<8} {'Total':<8} {'Experiments':<3}\n"
        )
        f.write("-" * 100 + "\n")

        grand_totals = {
            "optimal": 0,
            "timeout": 0,
            "infeasible": 0,
            "wrong_optimal": 0,
            "solver_error": 0,
            "missing": 0,
            "total": 0,
        }

        for strategy, data in strategy_aggregates.items():
            experiments_count = (
                len(data["experiments"]) if isinstance(data["experiments"], list) else 0
            )
            f.write(
                f"{strategy:<20} {data['optimal']:<8} {data['timeout']:<8} "
                f"{data['infeasible']:<10} {data['wrong_optimal']:<9} "
                f"{data['solver_error']:<10} {data['missing']:<8} "
                f"{data['total']:<8} {experiments_count:<3}\n"
            )

            # Add to grand totals
            for key in grand_totals:
                if key != "experiments":
                    grand_totals[key] += cast(int, data[key])

        f.write("-" * 100 + "\n")
        f.write(
            f"{'GRAND TOTAL':<20} {grand_totals['optimal']:<8} {grand_totals['timeout']:<8} "
            f"{grand_totals['infeasible']:<10} {grand_totals['wrong_optimal']:<9} "
            f"{grand_totals['solver_error']:<10} {grand_totals['missing']:<8} "
            f"{grand_totals['total']:<8}\n\n"
        )

        # Write experiment comparison
        f.write("EXPERIMENT COMPARISON\n")
        f.write("-" * 80 + "\n\n")

        f.write(
            f"{'Experiment':<30} {'Solver':<15} {'Optimal':<8} {'Timeout':<8} "
            f"{'Problems':<8} {'Total':<8}\n"
        )
        f.write("-" * 85 + "\n")

        for exp_key, totals in experiment_totals.items():
            exp_parts = exp_key.split("_", 1)
            if len(exp_parts) >= 2:
                exp_name = exp_parts[0]
                solver = exp_parts[1] if len(exp_parts) > 1 else "unknown"
            else:
                exp_name = exp_key
                solver = "unknown"

            solved = totals["optimal"]
            timeout = totals["timeout"]
            problems = (
                totals["total"] // len([s for s in strategy_aggregates.keys()])
                if len(strategy_aggregates) > 0
                else 0
            )
            total = totals["total"]

            f.write(
                f"{exp_name:<30} {solver:<15} {solved:<8} {timeout:<8} {problems:<8} {total:<8}\n"
            )

        f.write("\n" + "=" * 80 + "\n\n")

        # Performance insights
        f.write("PERFORMANCE INSIGHTS\n")
        f.write("-" * 80 + "\n\n")

        # Best strategy by optimal solutions
        if strategy_aggregates:
            best_strategy = max(
                strategy_aggregates.items(), key=lambda x: cast(int, x[1]["optimal"])
            )
            f.write(f"Best performing strategy (by optimal solutions): {best_strategy[0]}\n")
            f.write(f"  - Optimal solutions: {best_strategy[1]['optimal']}\n")
            optimal_val = cast(int, best_strategy[1]["optimal"])
            total_val = cast(int, best_strategy[1]["total"])
            f.write(f"  - Success rate: {optimal_val / total_val * 100:.1f}%\n\n")

            # Worst strategy by timeouts
            worst_timeout = max(
                strategy_aggregates.items(), key=lambda x: cast(int, x[1]["timeout"])
            )
            f.write(f"Strategy with most timeouts: {worst_timeout[0]}\n")
            f.write(f"  - Timeouts: {worst_timeout[1]['timeout']}\n")
            timeout_val = cast(int, worst_timeout[1]["timeout"])
            total_timeout_val = cast(int, worst_timeout[1]["total"])
            f.write(f"  - Timeout rate: {timeout_val / total_timeout_val * 100:.1f}%\n\n")

            # Strategy with most infeasible
            if any(cast(int, data["infeasible"]) > 0 for data in strategy_aggregates.values()):
                worst_infeasible = max(
                    strategy_aggregates.items(), key=lambda x: cast(int, x[1]["infeasible"])
                )
                f.write(f"Strategy with most infeasible solutions: {worst_infeasible[0]}\n")
                f.write(f"  - Infeasible: {worst_infeasible[1]['infeasible']}\n")
                infeasible_val = cast(int, worst_infeasible[1]["infeasible"])
                total_infeasible_val = cast(int, worst_infeasible[1]["total"])
                f.write(
                    f"  - Infeasible rate: {infeasible_val / total_infeasible_val * 100:.1f}%\n\n"
                )


def main() -> None:
    """Main function to orchestrate the aggregation process."""

    # Define paths - use relative path from the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    archive_dir = os.path.join(project_root, "data", "archive")
    output_file = os.path.join(archive_dir, "aggregated_solution_outcomes.txt")

    print("Starting solution outcomes aggregation...")
    print(f"Searching in: {archive_dir}")

    # Check if archive directory exists
    if not os.path.exists(archive_dir):
        print(f"Error: Archive directory not found at {archive_dir}")
        return

    # Find all solution_outcomes.txt files
    outcome_files = find_solution_outcome_files(archive_dir)

    if not outcome_files:
        print("No solution_outcomes.txt files found in the archive directory.")
        return

    print(f"Found {len(outcome_files)} solution_outcomes.txt files:")
    for file in outcome_files:
        print(f"  - {file}")

    # Parse all files
    print("\nParsing files...")
    parsed_data = []

    for file_path in outcome_files:
        print(f"  Parsing: {file_path}")
        data = parse_solution_outcomes_file(file_path)
        if data:
            parsed_data.append(data)
            non_total_strategies = [s for s in data["strategies"] if s["strategy"] != "TOTAL"]
            print(f"    Found {len(non_total_strategies)} strategies")
        else:
            print(f"    Warning: Failed to parse {file_path}")

    if not parsed_data:
        print("No files were successfully parsed.")
        return

    print(f"\nSuccessfully parsed {len(parsed_data)} files.")

    # Create aggregated report
    print(f"\nCreating aggregated report: {output_file}")
    create_aggregated_report(parsed_data, output_file)

    print("Aggregation complete!")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
