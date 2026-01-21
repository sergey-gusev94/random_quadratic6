#!/usr/bin/env python3
"""
Create a mapping from old model names to simplified new names.
Reads batch files and generates a JSON mapping file.
"""

import json
import os
from pathlib import Path


def read_batch_file(filepath):
    """Read a batch file and return list of model names."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    # Filter out empty lines and strip whitespace
    return [line.strip() for line in lines if line.strip()]


def create_name_mapping(batch_files, output_file):
    """
    Create a mapping from old names to new simplified names.
    
    Args:
        batch_files: Dictionary mapping batch type to filepath
                    e.g., {'conv': 'path/to/psd.txt', 'nonconv': 'path/to/nonconvex100.txt'}
        output_file: Path to output JSON file
    """
    mapping = {}
    
    for batch_type, filepath in batch_files.items():
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping...")
            continue
            
        models = read_batch_file(filepath)
        print(f"Processing {len(models)} models from {filepath} ({batch_type})")
        
        for idx, old_name in enumerate(models, start=1):
            # Create new name in format: rand_conv_1, rand_nonconv_1, etc.
            new_name = f"rand_{batch_type}_{idx}"
            mapping[old_name] = new_name
    
    # Write mapping to JSON file
    with open(output_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nCreated mapping with {len(mapping)} entries")
    print(f"Output saved to: {output_file}")
    
    return mapping


def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    batches_dir = script_dir.parent / "data" / "batches"
    
    # Default batch files
    batch_files = {
        'conv': batches_dir / "psd.txt",
        'nonconv': batches_dir / "nonconvex100.txt"
    }
    
    # Output file
    output_file = batches_dir / "name_mapping.json"
    
    print("Creating name mapping...")
    print(f"Batches directory: {batches_dir}")
    print(f"Input files:")
    for batch_type, filepath in batch_files.items():
        print(f"  {batch_type}: {filepath}")
    print(f"Output file: {output_file}\n")
    
    # Create the mapping
    mapping = create_name_mapping(batch_files, output_file)
    
    # Print some examples
    print("\nExample mappings:")
    for i, (old_name, new_name) in enumerate(mapping.items()):
        if i < 5:  # Show first 5
            print(f"  {old_name} -> {new_name}")
        else:
            break
    
    if len(mapping) > 5:
        print("  ...")
        # Show last 2
        items = list(mapping.items())
        for old_name, new_name in items[-2:]:
            print(f"  {old_name} -> {new_name}")


if __name__ == "__main__":
    main()

