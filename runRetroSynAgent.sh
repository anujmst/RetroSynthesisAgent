#!/bin/bash

python3 main.py --material flubendiamide --num_results 10 --alignment True --expansion True --filtration False --retrieval_mode patent-paper

# uvicorn vistree:app --reload
