#!/usr/bin/env python3
"""
Script to copy specific plot files from all archive folders.
Looks for these 4 specific files in each archive folder:
1. profile_absolute_performance_hull_exact_vs_hull.jpg
2. profile_absolute_performance.jpg  
3. profile_combined_hull_exact_vs_hull.jpg
4. profile_combined.jpg

Copies them to a new folder structure organized by archive folder name.
"""

import os
import shutil
from pathlib import Path


def main() -> None:
    # Define the base paths
    script_dir = Path(__file__).parent
    archive_dir = script_dir.parent / "data" / "archive"
    output_dir = script_dir.parent / "data" / "copied_plots"

    # The 4 specific files we're looking for
    target_files = [
        "profile_absolute_performance_hull_exact_vs_hull.jpg",
        "profile_absolute_performance.jpg",
        "profile_combined_hull_exact_vs_hull.jpg",
        "profile_combined.jpg",
        "dolan_more_profile.jpg",
        "dolan_more_profile_hull_exact_vs_hull.jpg",
    ]

    print(f"Archive directory: {archive_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Looking for files: {target_files}")
    print("=" * 50)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track statistics
    total_found = 0
    total_copied = 0

    # Iterate through all folders in archive directory
    if not archive_dir.exists():
        print(f"Error: Archive directory {archive_dir} does not exist!")
        return

    for archive_folder in archive_dir.iterdir():
        if not archive_folder.is_dir():
            continue

        print(f"\nProcessing archive folder: {archive_folder.name}")

        # Create output subfolder with archive folder name as prefix
        output_subfolder = output_dir / archive_folder.name
        output_subfolder.mkdir(parents=True, exist_ok=True)

        files_found_in_folder = 0
        files_copied_in_folder = 0

        # Recursively search for the target files in this archive folder
        for target_file in target_files:
            # Search recursively for this file
            found_files = list(archive_folder.rglob(target_file))

            for found_file in found_files:
                print(f"  Found: {found_file.relative_to(archive_dir)}")
                files_found_in_folder += 1
                total_found += 1

                # Create a descriptive filename with path info
                # Get the relative path from archive folder to help identify source
                rel_path = found_file.relative_to(archive_folder)
                # Replace path separators with underscores for filename
                path_part = str(rel_path.parent).replace(os.sep, "_")

                if path_part == ".":
                    # File is directly in archive folder
                    new_filename = f"{archive_folder.name}_{target_file}"
                else:
                    # File is in subdirectory
                    new_filename = f"{archive_folder.name}_{path_part}_{target_file}"

                output_file = output_subfolder / new_filename

                try:
                    shutil.copy2(found_file, output_file)
                    print(f"    -> Copied to: {output_file.relative_to(output_dir)}")
                    files_copied_in_folder += 1
                    total_copied += 1
                except Exception as e:
                    print(f"    -> Error copying: {e}")

        if files_found_in_folder == 0:
            print(f"  No target files found in {archive_folder.name}")
        else:
            print(
                f"  Summary: {files_found_in_folder} files found, "
                f"{files_copied_in_folder} files copied"
            )

    print("\n" + "=" * 50)
    print("FINAL SUMMARY:")
    print(f"Total files found: {total_found}")
    print(f"Total files copied: {total_copied}")
    print(f"Output directory: {output_dir}")

    # List what was created
    if output_dir.exists():
        print("\nCreated folders:")
        for subfolder in output_dir.iterdir():
            if subfolder.is_dir():
                file_count = len(list(subfolder.glob("*.jpg")))
                print(f"  {subfolder.name}/ ({file_count} files)")


if __name__ == "__main__":
    main()
