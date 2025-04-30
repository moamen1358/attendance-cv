#!/bin/bash

# Use the correct Python path that was detected
PYTHON_PATH="/media/invisa/inVisA/miniconda3/envs/test_/bin/python"
echo "Using Python from: $PYTHON_PATH"

# Run Streamlit with the correct Python path
$PYTHON_PATH -m streamlit run src/login.py "$@"
