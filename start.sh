#!/bin/bash
set -e

# This script is a generic entrypoint for the Face Recognition System (GPU mode)
# It is functionally identical to start_gpu.sh, but named for Docker compatibility.

cd /app

# Patch InsightFace to avoid cython issues
cp /app/insightface/python-package/insightface/app/__init__.py /app/insightface/python-package/insightface/app/__init__.py.backup 2>/dev/null || true

cat > /app/insightface/python-package/insightface/app/__init__.py << 'EOF'
from .face_analysis import *
# mask_renderer removed to avoid cython mesh_core_cython issues
EOF

# GPU Environment
export CUDA_VISIBLE_DEVICES=0
export GPU_MEMORY_FRACTION=0.8

# RTX 3050 4GB optimized config
if [ -f /app/src/performance_config.py ]; then
    echo "📋 Using existing performance configuration..."
    cat /app/src/performance_config.py | head -20
else
    echo "⚠️  Performance config not found, creating RTX 3050 4GB optimized version..."
    cat > /app/src/performance_config.py << 'EOF'
# RTX 3050 4GB Performance Configuration
INSIGHTFACE_MODEL = "antelopev2"  # High accuracy, fits in 4GB
YOLO_MODEL_SIZE = "l"  # Large model, fits in 4GB
DETECTION_SIZE = (640, 640)
CONFIDENCE_THRESHOLD = 0.4
MAX_FACES_PER_FRAME = 50
UI_UPDATE_INTERVAL = 3
SKIP_FRAME_INTERVAL = 1
CACHE_DURATION = 30
RECOGNITION_THRESHOLD = 0.65
AUTO_PERFORMANCE_ADJUST = False
TARGET_FPS = 12
VERBOSE_LOGGING = False
GPU_MODE = "BALANCED"  # For 4GB GPUs
CAMERA_BUFFER_SIZE = 2
USE_RTSP = False
RTSP_URL = 0
EOF
fi

echo "🚀 Starting Face Recognition System..."
echo "💾 GPU: NVIDIA GeForce MX250 (2GB VRAM)"
echo "⚙️ Mode: LOW_MEMORY optimized"

# Start application
exec streamlit run src/login.py --server.port=8501 --server.address=0.0.0.0
