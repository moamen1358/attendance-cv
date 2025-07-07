#!/bin/bash
set -e

echo "🚀 Face Recognition System - GPU Mode"
echo "Python: $(python3 --version)"
echo "Directory: $(pwd)"

# Check GPU
nvidia-smi || echo "⚠️ nvidia-smi not available, continuing..."

cd /app

# Patch InsightFace to avoid cython issues
echo "🔧 Applying InsightFace compatibility patch..."
cp /app/insightface/python-package/insightface/app/__init__.py /app/insightface/python-package/insightface/app/__init__.py.backup 2>/dev/null || true

cat > /app/insightface/python-package/insightface/app/__init__.py << 'EOF'
from .face_analysis import *
# mask_renderer removed to avoid cython mesh_core_cython issues
EOF

# GPU Environment
export CUDA_VISIBLE_DEVICES=0
export GPU_MEMORY_FRACTION=0.8
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Force float32 to avoid dtype mismatch
export CUDA_LAUNCH_BLOCKING=1
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
# Disable automatic mixed precision
export TORCH_CUDNN_V8_API_DISABLED=1

# Read current performance config to check user modifications
if [ -f /app/src/performance_config.py ]; then
    echo "📋 Using existing performance configuration..."
    cat /app/src/performance_config.py | head -20
else
    echo "⚠️  Performance config not found, creating GPU-optimized version..."
    cat > /app/src/performance_config.py << 'EOF'
# GPU Performance Configuration for MX250 (2GB)
INSIGHTFACE_MODEL = "buffalo_sc"  # Smaller model for 2GB GPU
YOLO_MODEL_SIZE = "s"  # Small model for limited GPU memory
DETECTION_SIZE = (416, 416)  # Balanced resolution
CONFIDENCE_THRESHOLD = 0.3
MAX_FACES_PER_FRAME = 2
UI_UPDATE_INTERVAL = 3
SKIP_FRAME_INTERVAL = 1
CACHE_DURATION = 30
RECOGNITION_THRESHOLD = 0.6
AUTO_PERFORMANCE_ADJUST = True
TARGET_FPS = 10
VERBOSE_LOGGING = False
GPU_MODE = "LOW_MEMORY"  # Essential for 2GB GPU
CAMERA_BUFFER_SIZE = 1
USE_RTSP = False
RTSP_URL = 0
EOF
fi

echo "🚀 Starting Face Recognition System..."
echo "💾 GPU: NVIDIA GeForce MX250 (2GB VRAM)"
echo "⚙️ Mode: LOW_MEMORY optimized"

# Start application
exec streamlit run src/login.py --server.port=8501 --server.address=0.0.0.0
