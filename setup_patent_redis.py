#!/usr/bin/env python3
"""
Script to import molecule_to_patent.jsonl data into Redis for use with PatentPDFDownloader.
"""
import json
import os
import sys
import redis
from tqdm import tqdm
import time
from rdkit import Chem

def clean_smile(smile):
    """
    Remove stereochemistry from SMILE string as it's not present in PatCID
    """
    try:
        mol = Chem.MolFromSmiles(smile)
        if mol is None:
            return None
        Chem.RemoveStereochemistry(mol)
        return Chem.MolToSmiles(mol, isomericSmiles=False)
    except Exception as e:
        print(f"Error processing SMILE string: {str(e)}")
        return None

def import_data_to_redis(jsonl_file, redis_host="localhost", redis_port=6379, redis_db=0, batch_size=1000):
    """
    Import data from molecule_to_patent.jsonl into Redis
    
    Args:
        jsonl_file: Path to the jsonl file
        redis_host: Redis host
        redis_port: Redis port
        redis_db: Redis database
        batch_size: Number of records to process in each batch
    """
    # Connect to Redis
    try:
        r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        r.ping()  # Test connection
        print(f"Connected to Redis at {redis_host}:{redis_port}, DB {redis_db}")
    except Exception as e:
        print(f"Error connecting to Redis: {str(e)}")
        print("Make sure Redis is running and accessible.")
        sys.exit(1)
    
    # Check if file exists
    if not os.path.exists(jsonl_file):
        print(f"Error: File {jsonl_file} not found.")
        print("Please download the file from https://doi.org/10.5281/zenodo.10572870 and place it in the project root.")
        sys.exit(1)
    
    # Count lines in file for progress bar
    with open(jsonl_file, 'r') as f:
        line_count = sum(1 for _ in f)
    
    print(f"Processing {line_count} records from {jsonl_file}")
    
    # Process file in batches
    batch = []
    processed = 0
    skipped = 0
    
    with open(jsonl_file, 'r') as f:
        for line in tqdm(f, total=line_count, desc="Processing records"):
            try:
                data = json.loads(line)
                smile = data.get("smile")
                patents = data.get("patents", [])
                
                if not smile or not patents:
                    skipped += 1
                    continue
                
                # Clean SMILE string
                cleaned_smile = clean_smile(smile)
                if not cleaned_smile:
                    skipped += 1
                    continue
                
                # Add to batch
                batch.append((cleaned_smile, patents))
                
                # Process batch if it reaches batch_size
                if len(batch) >= batch_size:
                    _process_batch(r, batch)
                    processed += len(batch)
                    batch = []
                    
            except json.JSONDecodeError:
                skipped += 1
                continue
            except Exception as e:
                print(f"Error processing record: {str(e)}")
                skipped += 1
                continue
    
    # Process remaining records
    if batch:
        _process_batch(r, batch)
        processed += len(batch)
    
    print(f"Import completed. Processed {processed} records, skipped {skipped} records.")
    print(f"Data is now available in Redis for use with PatentPDFDownloader.")

def _process_batch(redis_client, batch):
    """
    Process a batch of records
    
    Args:
        redis_client: Redis client
        batch: List of (smile, patents) tuples
    """
    pipe = redis_client.pipeline()
    
    for smile, patents in batch:
        key = f"smile:{smile}"
        pipe.set(key, json.dumps(patents))
    
    pipe.execute()

if __name__ == "__main__":
    # Default file path
    jsonl_file = "molecule_to_patent.jsonl"
    
    # Get Redis connection details from environment or command line
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(os.getenv("REDIS_DB", 0))
    
    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    if len(sys.argv) > 2:
        redis_host = sys.argv[2]
    if len(sys.argv) > 3:
        redis_port = int(sys.argv[3])
    if len(sys.argv) > 4:
        redis_db = int(sys.argv[4])
    
    # Import data
    import_data_to_redis(jsonl_file, redis_host, redis_port, redis_db)
