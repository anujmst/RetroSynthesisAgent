#!/bin/bash

# This script demonstrates the four different retrieval modes for RetroSynthesisAgent

# Check if a material name was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <material_name> [num_results]"
  echo "Example: $0 aspirin 10"
  exit 1
fi

MATERIAL=$1
NUM_RESULTS=${2:-10}  # Default to 10 if not provided

echo "===== Mode 1: Patent-Patent (Patents for both initial and expansion) ====="
python3 main.py --material "$MATERIAL" --num_results $NUM_RESULTS --alignment True --expansion True --filtration False --retrieval_mode patent-patent

echo "===== Mode 2: Paper-Paper (Academic papers for both initial and expansion) ====="
python3 main.py --material "$MATERIAL" --num_results $NUM_RESULTS --alignment True --expansion True --filtration False --retrieval_mode paper-paper

echo "===== Mode 3: Paper-Patent (Papers for initial, patents for expansion) ====="
python3 main.py --material "$MATERIAL" --num_results $NUM_RESULTS --alignment True --expansion True --filtration False --retrieval_mode paper-patent

echo "===== Mode 4: Patent-Paper (Patents for initial, papers for expansion) ====="
python3 main.py --material "$MATERIAL" --num_results $NUM_RESULTS --alignment True --expansion True --filtration False --retrieval_mode patent-paper

echo "All retrieval modes completed!"
