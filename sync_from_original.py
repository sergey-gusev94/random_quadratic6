#!/usr/bin/env python3
"""
Script to sync random_quadratic folder from the original project.
Deletes the local random_quadratic folder and copies from random_quadratic project.
"""

import shutil
from pathlib import Path


def main():
    script_dir = Path(__file__).parent
    
    target_dir = script_dir / "random_quadratic"
    source_dir = script_dir.parent / "random_quadratic" / "random_quadratic"
    
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    
    # Validate source exists
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return 1
    
    # Delete target if it exists
    if target_dir.exists():
        print(f"\nDeleting: {target_dir}")
        shutil.rmtree(target_dir)
        print("Deleted.")
    
    # Copy source to target
    print(f"\nCopying from source...")
    shutil.copytree(source_dir, target_dir)
    print("Done.")
    
    # Copy batches folder
    source_batches = script_dir.parent / "random_quadratic" / "data" / "batches"
    target_data = script_dir / "data"
    target_batches = target_data / "batches"
    
    print(f"\nSource batches: {source_batches}")
    print(f"Target batches: {target_batches}")
    
    # Validate source batches exists
    if not source_batches.exists():
        print(f"Warning: Source batches directory not found: {source_batches}")
        return 0
    
    # Create data directory if it doesn't exist
    target_data.mkdir(parents=True, exist_ok=True)
    
    # Delete target batches if it exists
    if target_batches.exists():
        print(f"\nDeleting: {target_batches}")
        shutil.rmtree(target_batches)
        print("Deleted.")
    
    # Copy batches folder
    print(f"\nCopying batches folder...")
    shutil.copytree(source_batches, target_batches)
    print("Done.")
    
    return 0


if __name__ == "__main__":
    exit(main())
