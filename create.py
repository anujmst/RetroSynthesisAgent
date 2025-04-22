import gzip
import json
import os
import sys

# --- Configuration ---
# ADJUST THIS if your downloaded filename is different
INPUT_FILENAME = "version.smi.gz" 
OUTPUT_FILENAME = os.path.join("RetroSynAgent", "emol.json")
# Some .smi files use tabs, some use spaces. Adjust if needed.
SEPARATOR = '\t' 
# --- End Configuration ---

def create_emolecules_json():
    """
    Reads a gzipped SMILES file from eMolecules, extracts SMILES strings,
    and saves them as a JSON list to the specified output file.
    """
    if not os.path.exists(INPUT_FILENAME):
        print(f"Error: Input file '{INPUT_FILENAME}' not found.")
        print("Please download the eMolecules free dataset (e.g., version-2024-07-01.smi.gz)")
        print(f"from https://downloads.emolecules.com/free/ and place it here.")
        sys.exit(1)

    print(f"Processing '{INPUT_FILENAME}'...")
    smiles_set = set()
    processed_lines = 0
    skipped_lines = 0

    try:
        # Open the gzipped file for reading in text mode
        with gzip.open(INPUT_FILENAME, 'rt', encoding='utf-8') as f_in:
            for line in f_in:
                processed_lines += 1
                parts = line.strip().split(SEPARATOR)
                if parts:
                    smiles = parts[0] # Assume SMILES is the first part
                    if smiles: # Ensure it's not empty
                        smiles_set.add(smiles)
                    else:
                        skipped_lines +=1
                else:
                    skipped_lines +=1
                
                if processed_lines % 100000 == 0:
                    print(f"  Processed {processed_lines:,} lines...")

    except Exception as e:
        print(f"Error reading or processing file: {e}")
        sys.exit(1)

    print(f"Finished processing. Total lines: {processed_lines:,}, Skipped/Empty: {skipped_lines:,}")
    print(f"Unique SMILES found: {len(smiles_set):,}")

    # Convert set to list for JSON serialization
    smiles_list = list(smiles_set)

    # Ensure the output directory exists
    output_dir = os.path.dirname(OUTPUT_FILENAME)
    if not os.path.exists(output_dir):
        print(f"Creating directory: {output_dir}")
        os.makedirs(output_dir) # Should already exist, but good practice

    print(f"Saving unique SMILES list to '{OUTPUT_FILENAME}'...")
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f_out:
            json.dump(smiles_list, f_out)
        print("Successfully created emol.json!")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_emolecules_json()