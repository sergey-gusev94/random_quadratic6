import datetime
import os
import re
from typing import Dict, List, Optional, Tuple

import pandas as pd


def parse_root_relaxation(
    output_log_path: str, solver: str = "gams", subsolver: str = "baron"
) -> Optional[float]:
    """
    Parse the output log file to extract the root relaxation objective value.
    This is a simplified version of the function in solve.py, focused on BARON and Gurobi.

    Parameters
    ----------
    output_log_path : str
        Path to the output log file
    solver : str
        The solver used (default: "gams")
    subsolver : str
        The subsolver used (default: "baron")

    Returns
    -------
    Optional[float]
        The root relaxation objective value if found, None otherwise
    """
    if not os.path.exists(output_log_path):
        return None

    try:
        with open(output_log_path, "r") as f:
            log_content = f.read()

        # Check for Gurobi (through GAMS or direct)
        if subsolver and subsolver.lower() == "gurobi" or solver.lower() == "gurobi":
            # Pattern 1: Standard root relaxation
            gurobi_match = re.search(
                r"Root relaxation: objective\s+([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content
            )
            if gurobi_match:
                root_relaxation = float(gurobi_match.group(1))
                return root_relaxation

            # Pattern 2: Root relaxation cutoff with table
            cutoff_match = re.search(r"Root relaxation: cutoff", log_content)
            if cutoff_match:
                # Look for the nodes table that follows
                nodes_table_match = re.search(
                    r"Nodes\s+\|\s+Current Node\s+\|\s+Objective Bounds", log_content
                )
                if nodes_table_match:
                    # Find the first data line in this table
                    table_end = nodes_table_match.end()
                    table_content = log_content[table_end:]
                    lines = table_content.strip().split("\n")

                    for line in lines:
                        if re.search(r"^\s+\d+\s+\d+", line):  # Line starts with node numbers
                            # Extract numeric values
                            values = []
                            for part in line.split():
                                try:
                                    values.append(float(part))
                                except ValueError:
                                    pass

                            # BestBd is typically the second-to-last numeric value
                            if len(values) >= 2:
                                bound_value = values[-2]  # Second to last numeric value
                                return bound_value
                            break

            # Pattern 3: Single node exploration with best bound
            single_node_match = re.search(r"Explored \d+ nodes?", log_content)
            best_bound_match = re.search(
                r"[Bb]est bound ([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content
            )

            if single_node_match and best_bound_match:
                bound_value = float(best_bound_match.group(1))
                return bound_value

            # Pattern 4: Extract from gap line at the end
            gap_line_match = re.search(
                r"[Bb]est objective [-+]?\d*\.\d+(?:[eE][-+]?\d+)?,"
                + r" best bound ([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)",
                log_content,
            )

            if gap_line_match:
                bound_value = float(gap_line_match.group(1))
                return bound_value

        # Check for BARON through GAMS
        if solver.lower() == "gams" and subsolver and subsolver.lower() == "baron":
            # Find the standard iteration table header
            header_match = re.search(
                r"Iteration\s+Time[^\\n]*Lower bound\s+Upper bound\s+Progress", log_content
            )

            if header_match:
                # We found the header line
                header_end = header_match.end()

                # Get the portion of the log after this header
                post_header = log_content[header_end:]

                # Find the first non-empty line after the header
                lines = post_header.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("==="):
                        continue

                    # Extract values directly using regex to ensure correct column is identified
                    # Pattern: [iteration] [time] [memory] [lower bound] [upper bound] [progress]
                    match = re.search(
                        r"\s*\S+\s+\S+\s+\S+\s+([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)\s+", line
                    )
                    if match:
                        lower_bound = float(match.group(1))
                        return lower_bound

                    # Fallback: if regex match didn't work, try the old way with adjusted indexes
                    parts = line.split()
                    if (
                        len(parts) >= 5
                    ):  # Need at least iteration, time, memory, lower bound, upper bound
                        try:
                            # Try to directly access the lower bound column (the 4th column)
                            lower_bound = float(parts[3])  # 0-indexed, so 3 is the 4th column
                            return lower_bound
                        except ValueError:
                            # If that failed, try the original numeric extraction approach
                            numeric_parts = []
                            for part in parts:
                                try:
                                    value = float(part)
                                    numeric_parts.append(value)
                                except ValueError:
                                    # Not a number, skip
                                    pass

                            if len(numeric_parts) >= 3:
                                # If memory isn't a clean number (e.g., "32MB"),
                                # the lower bound will be the 3rd numeric value
                                lower_bound = numeric_parts[2]
                                return lower_bound

            # Check for "Problem solved during preprocessing" case - extract "Best possible" value
            preprocessing_match = re.search(r"Problem solved during preprocessing", log_content)
            if preprocessing_match:
                best_possible_match = re.search(
                    r"Best possible = ([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content
                )
                if best_possible_match:
                    best_possible = float(best_possible_match.group(1))
                    return best_possible

                # Alternative: Look for "Lower bound is" value
                lower_bound_match = re.search(
                    r"Lower bound is\s+([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content
                )
                if lower_bound_match:
                    lower_bound = float(lower_bound_match.group(1))
                    return lower_bound

        return None
    except Exception:
        return None


def extract_original_objective(output_log_path: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extract the original objective value from the output log file.

    Parameters
    ----------
    output_log_path : str
        Path to the output log file

    Returns
    -------
    Tuple[Optional[float], Optional[str]]
        A tuple containing:
        - The original objective value if found, None otherwise
        - The solution text if found, None otherwise
    """
    if not os.path.exists(output_log_path):
        return None, None

    try:
        with open(output_log_path, "r") as f:
            log_content = f.read()

        solution_text = None
        solution_value = None

        # Look for lines like "Original objective value: X"
        match = re.search(
            r"Original objective value:\s*([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content
        )
        if match:
            solution_value = float(match.group(1))
            solution_text = match.group(0)

        # Alternative: Look for Solution = X
        if not solution_value:
            match = re.search(r"Solution\s*=\s*([-+]?\d*\.\d+(?:[eE][-+]?\d+)?)", log_content)
            if match:
                solution_value = float(match.group(1))
                solution_text = match.group(0)

        return solution_value, solution_text
    except Exception as e:
        print(f"Error extracting objective: {str(e)}")
        return None, None


def calculate_gaps(original_obj: float, root_relaxation: float) -> Tuple[float, Optional[float]]:
    """
    Calculate both absolute and relative relaxation gaps.

    Parameters
    ----------
    original_obj : float
        Objective value of the original problem
    root_relaxation : float
        Root relaxation objective value

    Returns
    -------
    Tuple[float, Optional[float]]
        A tuple containing (absolute_gap, relative_gap_percent)
        - absolute_gap: |original - relaxation|
        - relative_gap_percent: |original - relaxation| / |original| * 100%
    """
    # Calculate absolute gap
    abs_gap = abs(original_obj - root_relaxation)

    # Calculate relative gap as a percentage
    rel_gap = None
    if original_obj != 0:
        rel_gap = abs_gap / abs(original_obj) * 100.0

    return abs_gap, rel_gap


def extract_datetime_from_path(path: str) -> Optional[datetime.datetime]:
    """
    Extract datetime from folder path like '2025-05-07_21-45-37'

    Parameters
    ----------
    path : str
        The path string that might contain a datetime pattern

    Returns
    -------
    Optional[datetime.datetime]
        The extracted datetime object, or None if not found
    """
    # Extract all directory components from the path
    path_parts = path.split(os.path.sep)

    # Look for a component matching the datetime pattern YYYY-MM-DD_HH-MM-SS
    date_pattern = r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})"

    for part in path_parts:
        match = re.match(date_pattern, part)
        if match:
            dt_str = match.group(1)
            try:
                # Convert to datetime object
                return datetime.datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
            except ValueError:
                pass

    return None


def parse_excel_datetime(dt_str: str) -> Optional[datetime.datetime]:
    """
    Parse Excel datetime string into datetime object.

    Parameters
    ----------
    dt_str : str
        Datetime string from Excel

    Returns
    -------
    Optional[datetime.datetime]
        The parsed datetime object, or None if not parseable
    """
    if pd.isna(dt_str):
        return None

    # Try different datetime formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # 2025-05-07 21:45:37
        "%m/%d/%Y %H:%M:%S",  # 5/7/2025 21:45:37
        "%m/%d/%Y %I:%M:%S %p",  # 5/7/2025 9:45:37 PM
        "%Y-%m-%d_%H-%M-%S",  # 2025-05-07_21-45-37
        "%Y%m%d_%H%M%S",  # 20250507_214537
    ]

    for fmt in formats:
        try:
            return datetime.datetime.strptime(str(dt_str), fmt)
        except ValueError:
            continue

    # If we get here, none of the formats worked
    return None


def scan_results_directory(base_dir: str) -> List[Dict]:
    """
    Scan the results directory structure to find all result folders and their log files.

    Parameters
    ----------
    base_dir : str
        Base directory to start scanning from

    Returns
    -------
    List[Dict]
        List of dictionaries containing information about each result
        Each dictionary includes paths, solver info, and strategy
    """
    results = []

    # Look for solver directories matching pattern "gams_*" or "gurobi_*"
    solver_dirs = []
    for item in os.listdir(base_dir):
        if os.path.isdir(os.path.join(base_dir, item)) and (
            item.startswith("gams_") or item.startswith("gurobi_")
        ):
            solver_dirs.append(os.path.join(base_dir, item))

    print(f"Found {len(solver_dirs)} solver directories")

    for solver_dir in solver_dirs:
        # Extract solver info and strategy from the directory name
        solver_info = os.path.basename(solver_dir)
        solver_parts = solver_info.split("_", 1)

        # First part is always the solver name
        solver = solver_parts[0]  # gams or gurobi

        # If we have a second part, it may contain subsolver and/or strategy
        if len(solver_parts) > 1:
            rest = solver_parts[1]

            # Check if this includes a gdp strategy
            if "gdp." in rest:
                # Format could be like "baron_gdp.hull" or just "gdp.hull"
                if "_gdp." in rest:
                    # Subsolver and strategy
                    subsolver, strategy = rest.split("_gdp.", 1)
                    strategy = "gdp." + strategy
                else:
                    # Just strategy, no subsolver
                    subsolver = None
                    strategy = "gdp." + rest.split("gdp.", 1)[1]
            else:
                # No strategy, just subsolver
                subsolver = rest
                strategy = None
        else:
            # No subsolver or strategy
            subsolver = None
            strategy = None

        # Look for mode directories (approximation, exact, no_mode, etc.)
        try:
            for mode_dir in os.listdir(solver_dir):
                mode_path = os.path.join(solver_dir, mode_dir)
                if os.path.isdir(mode_path):
                    # Each date-time subdirectory is a specific run
                    run_dirs = []
                    for run_dir in os.listdir(mode_path):
                        run_path = os.path.join(mode_path, run_dir)
                        if os.path.isdir(run_path):
                            run_dirs.append(run_dir)

                    for run_dir in run_dirs:
                        run_path = os.path.join(mode_path, run_dir)

                        # Extract datetime from the run directory path
                        run_datetime = extract_datetime_from_path(run_path)

                        # Check for "original" directory
                        original_dir = os.path.join(run_path, "original")

                        # Debug what's in the run directory
                        run_contents = os.listdir(run_path) if os.path.exists(run_path) else []
                        has_original = "original" in run_contents

                        original_log = os.path.join(original_dir, "output_log.txt")
                        has_original_log = os.path.exists(original_log)

                        # We only need the original log, not the relaxed log
                        if has_original and has_original_log:
                            # Everything looks good, add to results
                            results.append(
                                {
                                    "solver": solver,
                                    "subsolver": subsolver,
                                    "strategy": strategy,
                                    "mode": mode_dir,
                                    "run_dir": run_dir,
                                    "original_log": original_log,
                                    "base_path": run_path,
                                    "run_datetime": run_datetime,
                                }
                            )

        except Exception:
            pass

    return results


def scan_output_logs_directly(base_dir: str) -> List[Dict]:
    """
    Alternative approach: search directly for output_log.txt files using glob.

    Parameters
    ----------
    base_dir : str
        Base directory to start scanning from

    Returns
    -------
    List[Dict]
        List of dictionaries containing information about each found log file
    """
    import glob

    results = []

    # Find all output_log.txt files under the base directory
    log_pattern = os.path.join(base_dir, "**", "output_log.txt")
    output_logs = glob.glob(log_pattern, recursive=True)

    print(f"Found {len(output_logs)} output_log.txt files using glob")

    # Process each log file path to extract information
    for log_path in output_logs:
        try:
            # Analyze the path structure
            path_parts = log_path.split(os.path.sep)

            # Try to identify key parts based on path structure
            log_dir = os.path.dirname(log_path)
            problem_type = os.path.basename(log_dir)  # Should be "original" or "relaxed"

            # Only process "original" logs
            if problem_type != "original":
                continue

            # Extract datetime from the path
            run_datetime = extract_datetime_from_path(log_path)

            # Extract information from the path
            # Find the index of the data directory
            data_index = path_parts.index("data") if "data" in path_parts else -1

            if data_index >= 0 and data_index + 4 < len(path_parts):
                # Expected structure:
                # .../data/solver_subsolver_strategy/mode/run_date/original/output_log.txt
                solver_info = path_parts[data_index + 1]
                mode = path_parts[data_index + 2]
                run_dir = path_parts[data_index + 3]

                # Parse solver info
                if "_" in solver_info:
                    solver_parts = solver_info.split("_", 1)
                    solver = solver_parts[0]
                    rest = solver_parts[1] if len(solver_parts) > 1 else ""

                    # Check for gdp pattern
                    if "gdp." in rest:
                        if "_gdp." in rest:
                            subsolver, strategy = rest.split("_gdp.", 1)
                            strategy = "gdp." + strategy
                        else:
                            subsolver = None
                            strategy = "gdp." + rest.split("gdp.", 1)[1]
                    else:
                        subsolver = rest
                        strategy = None
                else:
                    solver = solver_info
                    subsolver = None
                    strategy = None

                # Add to results
                results.append(
                    {
                        "solver": solver,
                        "subsolver": subsolver,
                        "strategy": strategy,
                        "mode": mode,
                        "run_dir": run_dir,
                        "original_log": log_path,
                        "base_path": os.path.dirname(log_dir),
                        "run_datetime": run_datetime,
                    }
                )
        except Exception:
            pass

    print(f"Found {len(results)} valid original logs")
    return results


def extract_root_data(
    log_path: str, solver: str, subsolver: str
) -> Optional[Tuple[float, float, float, Optional[float], float, Optional[str]]]:
    """
    Extract root relaxation data from a log file.

    Parameters
    ----------
    log_path : str
        Path to the log file
    solver : str
        Solver used (e.g., 'gams')
    subsolver : str
        Subsolver used (e.g., 'baron')

    Returns
    -------
    Optional[Tuple[float, float, float, Optional[float], float, Optional[str]]]
        Tuple of (root_relaxation, original_obj, abs_gap, rel_gap,
        solution_value, solution_text) if successful, None otherwise
    """
    try:
        # Extract root relaxation value from the original log
        root_relaxation = parse_root_relaxation(log_path, solver, subsolver)
        if root_relaxation is None:
            return None

        # Extract original objective value and solution text
        original_obj, solution_text = extract_original_objective(log_path)
        if original_obj is None:
            return None

        # Calculate the correct gaps
        abs_gap, rel_gap = calculate_gaps(original_obj, root_relaxation)

        return root_relaxation, original_obj, abs_gap, rel_gap, original_obj, solution_text
    except Exception:
        return None


def normalize_strategy_name(strategy: Optional[str]) -> Optional[str]:
    """
    Normalize the strategy name for consistent comparison.

    Parameters
    ----------
    strategy : Optional[str]
        The strategy name to normalize

    Returns
    -------
    Optional[str]
        The normalized strategy name
    """
    if strategy is None:
        return None

    # Convert to lowercase for case-insensitive comparison
    strategy = strategy.lower()

    # Handle common variations of strategy names
    if strategy.startswith("gdp."):
        # Keep the full strategy name, don't modify it
        return strategy

    return strategy


def fix_relaxation_gaps(excel_path: str, results_dir: str, dry_run: bool = False) -> None:
    """
    Main function to fix relaxation gaps in Excel results file.

    Parameters
    ----------
    excel_path : str
        Path to the Excel results file
    results_dir : str
        Directory containing all result folders
    dry_run : bool, optional
        If True, don't modify the Excel file, just print what would be changed
    """
    # Load the Excel file
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return

    try:
        df = pd.read_excel(excel_path)
        original_rows = df[df["Problem Type"] == "Original"]
        # Add tracking column to identify matched rows
        df["_matched"] = False
        print(f"Loaded Excel file with {len(df)} rows")
        print(f"Found {len(original_rows)} rows with Problem Type = 'Original'")
    except Exception as e:
        print(f"Error loading Excel file: {str(e)}")
        return

    # Try both scanning methods
    print("\n=== Scanning for result directories ===")
    results = scan_results_directory(results_dir)

    if len(results) == 0:
        print(
            "\n=== No results found with directory structure "
            "method, trying direct log file search ==="
        )
        results = scan_output_logs_directly(results_dir)

    print(f"Found {len(results)} result directories to process")

    # Process all results and build a lookup dictionary
    results_by_key: Dict[Tuple[str, str, Optional[str]], List[Dict]] = {}
    for result in results:
        # Normalize strategy name
        strategy = normalize_strategy_name(result["strategy"])

        # Create a lookup key based on solver, mode, strategy
        key: Tuple[str, str, Optional[str]] = (
            result["solver"].lower() if result["solver"] is not None else "",
            result["mode"].lower() if result["mode"] is not None else "",
            strategy,
        )

        # If this is the first result with this key, initialize a list
        if key not in results_by_key:
            results_by_key[key] = []

        # Add this result to the list for the key
        results_by_key[key].append(result)

    # Print all keys for debugging
    print("\n=== Available keys in result folders ===")
    for key in sorted(results_by_key.keys()):
        print(f"  {key}")

    # For each key, sort results by datetime (oldest first)
    for key in results_by_key:
        results_by_key[key].sort(
            key=lambda x: x["run_datetime"] if x["run_datetime"] else datetime.datetime.max
        )

    # Track changes
    changes_made = 0
    already_correct = 0
    errors = 0
    matched_rows = 0
    not_matched_rows = 0
    no_time_in_excel = 0
    solution_mismatches = 0
    timestamp_issues = 0

    # Process each Excel row with "Original" problem type
    for idx, row in original_rows.iterrows():
        try:
            # Extract Excel row's run time
            excel_run_time = None
            if "Run Time" in row:
                excel_run_time = parse_excel_datetime(row["Run Time"])

            if excel_run_time is None:
                no_time_in_excel += 1

            # Get solver, mode, strategy from Excel (case-insensitive)
            solver = str(row["Solver"]).lower() if pd.notna(row["Solver"]) else None
            mode = str(row["Mode"]).lower() if pd.notna(row["Mode"]) else None
            strategy = normalize_strategy_name(
                row["Strategy"] if pd.notna(row["Strategy"]) else None
            )

            # Create a lookup key - all components must match exactly
            row_key: Tuple[str, str, Optional[str]] = (
                solver if solver is not None else "",
                mode if mode is not None else "",
                strategy,
            )

            print(f"\nProcessing row {idx} with key: {row_key}")

            # Only look for exact key match - no partial matching
            if row_key not in results_by_key:
                print(f"  No exact match found for key: {row_key}")
                not_matched_rows += 1
                continue

            # Get all candidate results with matching key
            candidate_results = results_by_key[row_key].copy()
            print(f"  Found {len(candidate_results)} candidates with matching key")

            # If we have an Excel runtime, validate all candidates have run_datetime
            if excel_run_time:
                # Debugging: print candidate timestamps
                print(f"  Timestamp analysis (Excel time: {excel_run_time}):")
                for i, r in enumerate(candidate_results):
                    print(f"    Candidate {i+1}: {r['run_datetime']} - {r['original_log']}")

                # Find the most recent result that's still before Excel run time
                valid_results = []
                for r in candidate_results:
                    if r["run_datetime"] is None:
                        print(f"    Warning: Candidate has no timestamp: {r['original_log']}")
                        continue

                    # NOT Strict check: folder time must be strictly EARLIER
                    # or equal than Excel time
                    if r["run_datetime"] <= excel_run_time:
                        time_diff = excel_run_time - r["run_datetime"]
                        print(
                            "    Valid: "
                            f"{r['run_datetime']} is "
                            f"{time_diff.total_seconds()} seconds before Excel time"
                        )
                        valid_results.append(r)
                    else:
                        time_diff = r["run_datetime"] - excel_run_time
                        print(
                            "    Invalid: "
                            f"{r['run_datetime']} is "
                            f"{time_diff.total_seconds()} seconds AFTER Excel time"
                        )

                if valid_results:
                    # Sort by datetime descending (most recent first)
                    valid_results.sort(key=lambda x: x["run_datetime"], reverse=True)
                    best_result = valid_results[0]
                    print(
                        "    Selected: "
                        f"{best_result['run_datetime']} - {best_result['original_log']}"
                    )
                else:
                    print("    No valid results with timestamp before Excel run time")
                    timestamp_issues += 1
                    not_matched_rows += 1
                    continue
            else:
                # If no Excel run time, take the first (oldest) result
                best_result = candidate_results[0]
                print(f"    No Excel run time, using oldest result: {best_result['original_log']}")

            # If we found a matching folder, process it
            if best_result:
                # Mark this row as matched
                df.at[idx, "_matched"] = True
                matched_rows += 1

                # Extract data from the log file
                log_data = extract_root_data(
                    best_result["original_log"], best_result["solver"], best_result["subsolver"]
                )

                if log_data:
                    (
                        root_relaxation,
                        original_obj,
                        abs_gap,
                        rel_gap,
                        solution_value,
                        solution_text,
                    ) = log_data

                    # Get existing objective value from Excel
                    excel_objective = None
                    if "Objective Value" in row and pd.notna(row["Objective Value"]):
                        try:
                            excel_objective = float(row["Objective Value"])
                        except (ValueError, TypeError):
                            pass

                    # Check if solutions match with a more generous tolerance (1e-6)
                    if excel_objective is not None and abs(excel_objective - solution_value) > 1e-6:
                        print("  SOLUTION MISMATCH:")
                        print(f"    Excel objective: {excel_objective}")
                        print(f"    Log solution: {solution_value} ({solution_text})")
                        print(f"    Difference: {abs(excel_objective - solution_value)}")
                        print(f"    File: {best_result['original_log']}")
                        solution_mismatches += 1
                        # Skip this row - don't update it
                        continue

                    # Check if values need to be updated
                    current_root_relax = row["Root Relaxation Value"]
                    current_rel_gap = row["Root Relaxation Gap (%)"]

                    has_mismatch = False

                    # Check if root relaxation value is different,
                    # using a more appropriate tolerance
                    if pd.isna(current_root_relax):
                        has_mismatch = True
                    elif abs(float(current_root_relax) - root_relaxation) > 1e-4:
                        has_mismatch = True

                    # Check if relative gap is different
                    if pd.isna(current_rel_gap):
                        has_mismatch = True
                    elif rel_gap is not None and abs(float(current_rel_gap) - rel_gap) > 1e-4:
                        has_mismatch = True

                    if has_mismatch:
                        print(
                            "  Updating row with new values: "
                            f"Root Relaxation = {root_relaxation}, Gap = {rel_gap}"
                        )
                        if not dry_run:
                            # Update the row with correct values
                            df.at[idx, "Root Relaxation Value"] = root_relaxation
                            df.at[idx, "Root Relaxation Gap (%)"] = rel_gap
                            changes_made += 1
                    else:
                        print("  Values already correct")
                        already_correct += 1
                else:
                    print("  Error: Could not extract data from log file")
                    errors += 1
            else:
                not_matched_rows += 1

        except Exception as e:
            print(f"Error processing Excel row {idx}: {str(e)}")
            errors += 1

    # Print one-to-one matching statistics
    print("\n=== Excel Row Matching Statistics ===")
    print(f"Total Excel rows with Problem Type = Original: {len(original_rows)}")
    print(f"Excel rows matched to a folder: {matched_rows}")
    print(f"Excel rows not matched to any folder: {not_matched_rows}")
    print(f"Excel rows with no Run Time: {no_time_in_excel}")
    print(f"Solution mismatches detected: {solution_mismatches}")
    print(f"Timestamp issues detected: {timestamp_issues}")

    # Save the updated Excel file if changes were made
    if changes_made > 0 and not dry_run:
        backup_path = excel_path.replace(
            ".xlsx", f"_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        df.to_excel(backup_path, index=False)
        print(f"Saved backup to {backup_path}")

        df.to_excel(excel_path, index=False)
        print(f"Updated Excel file saved to {excel_path}")

    # Print summary
    print("\n=== Summary ===")
    print(f"  Processed {len(original_rows)} Excel rows with Problem Type = Original")
    print(f"  Found {len(results)} result directories")
    print(f"  Changes made: {changes_made}")
    print(f"  Already correct: {already_correct}")
    print(f"  Solution mismatches: {solution_mismatches}")
    print(f"  Timestamp issues: {timestamp_issues}")
    print(f"  Errors: {errors}")

    # Report on unmatched Excel rows
    unmatched_rows = df[(df["Problem Type"] == "Original") & (~df["_matched"])]
    print(f"  Excel rows with no matching calculation results: {len(unmatched_rows)}")

    if len(unmatched_rows) > 0:
        print("\nExcel rows without matching calculation results:")
        for idx, row in unmatched_rows.iterrows():
            print(
                "  Row {}: Strategy={}, " "Mode={}, Solver={}".format(
                    idx, row["Strategy"], row["Mode"], row["Solver"]
                )
            )

    # Remove the tracking column before saving
    if "_matched" in df.columns:
        df = df.drop(columns=["_matched"])


if __name__ == "__main__":
    # Directory containing the data folder - we only need to go up one level, not two
    base_dir = os.path.dirname(os.getcwd())

    # Check if we're in the right directory structure
    if not os.path.exists(os.path.join(base_dir, "data")):
        # Try using the current directory as base
        base_dir = os.getcwd()
        if not os.path.exists(os.path.join(base_dir, "data")):
            # Try one more possibility - current directory might be the project directory
            data_dir = os.path.join(base_dir, "random_quadratic", "data")
            if os.path.exists(data_dir):
                base_dir = os.path.join(base_dir, "random_quadratic")

    # Path to Excel file
    excel_path = os.path.join(base_dir, "data", "results.xlsx")

    # If the Excel file doesn't exist, look for it in neighboring directories
    if not os.path.exists(excel_path):
        print(f"Excel file not found at {excel_path}")
        # Look for it in the current directory
        alt_excel_path = "results.xlsx"
        if os.path.exists(alt_excel_path):
            excel_path = alt_excel_path
            print(f"Found Excel file at {excel_path}")
        else:
            # Look for it in the data directory
            for root, dirs, files in os.walk(os.path.join(base_dir, "data")):
                for file in files:
                    if file == "results.xlsx":
                        excel_path = os.path.join(root, file)
                        print(f"Found Excel file at {excel_path}")
                        break
                if os.path.exists(excel_path):
                    break

    # Path to results directory
    results_dir = os.path.join(base_dir, "data")

    print(f"Excel path: {excel_path}")
    print(f"Results directory: {results_dir}")

    # First do a dry run to see what would be changed
    print("\nDry run (no changes will be made):\n")
    fix_relaxation_gaps(excel_path, results_dir, dry_run=True)

    # Ask for confirmation
    response = input("\nDo you want to proceed with making these changes? (y/n): ")
    if response.lower() == "y":
        print("\nApplying changes...\n")
        fix_relaxation_gaps(excel_path, results_dir, dry_run=False)
    else:
        print("\nAborted. No changes were made.")
