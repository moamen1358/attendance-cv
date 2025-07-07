#!/bin/bash

# Use the correct Python path that was detected
# PYTHON_PATH="/media/invisa/inVisA/miniconda3/envs/test_/bin/python"    #for ssd
PYTHON_PATH="/home/invisa/miniconda3/envs/test_/bin/python"
echo "Using Python from: $PYTHON_PATH"

# GPU Environment variables to fix dtype mismatch
export CUDA_VISIBLE_DEVICES=0
export GPU_MEMORY_FRACTION=0.8
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Force float32 to avoid dtype mismatch
export CUDA_LAUNCH_BLOCKING=1
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
# Disable automatic mixed precision
export TORCH_CUDNN_V8_API_DISABLED=1

echo "🚀 Environment configured for dtype consistency"

# Run Streamlit with the correct Python path
$PYTHON_PATH -m streamlit run src/login.py "$@"
