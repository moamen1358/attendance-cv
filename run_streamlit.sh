#!/bin/bash

# Use the direct Python path to run Streamlit instead of relying on the streamlit command
PYTHON_PATH="/media/invisa/inVisA/miniconda3/envs/test_/bin/python"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Make sure the Python path exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Python not found at $PYTHON_PATH"
    echo "Please check the path and try again."
    exit 1
fi

# Run Streamlit using the Python module approach
echo "Starting Streamlit using Python path: $PYTHON_PATH"
"$PYTHON_PATH" -m streamlit run "$SCRIPT_DIR/src/login.py" "$@"
