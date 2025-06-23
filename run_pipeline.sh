#!/bin/bash

# Simple wrapper script to run the pipeline

# Activate virtual environment (if used)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Run the pipeline with example arguments
python main.py \
    "data/input/science_article.pdf" \
    --source-type pdf \
    --topic "The Science of Climate Change" \
    # --schedule "0 9 * * *"  # Uncomment for daily runs at 9AM

# Deactivate virtual environment (if used)
if [ -d "venv" ]; then
    deactivate
fi
