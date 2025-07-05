#!/bin/bash

# System Status Checker for Face Recognition App
echo "🔍 Face Recognition App - System Status Check"
echo "=============================================="

# Check Docker
echo "🐳 Docker Status:"
if command -v docker &> /dev/null; then
    echo "  ✅ Docker installed: $(docker --version)"
    if docker ps &> /dev/null; then
        echo "  ✅ Docker daemon running"
        running_containers=$(docker ps --filter "publish=8501" --format "table {{.Names}}\t{{.Status}}")
        if [ -n "$running_containers" ]; then
            echo "  📱 Running containers on port 8501:"
            echo "$running_containers"
        else
            echo "  📱 No containers running on port 8501"
        fi
    else
        echo "  ❌ Docker daemon not running"
    fi
else
    echo "  ❌ Docker not installed"
fi

echo ""

# Check Python environment
echo "🐍 Python Environment:"
if command -v python &> /dev/null; then
    echo "  ✅ Python installed: $(python --version)"
    if python -c "import streamlit" &> /dev/null; then
        echo "  ✅ Streamlit available"
    else
        echo "  ❌ Streamlit not available"
    fi
else
    echo "  ❌ Python not found"
fi

echo ""

# Check GPU
echo "🚀 GPU Status:"
if command -v nvidia-smi &> /dev/null; then
    echo "  ✅ NVIDIA drivers installed"
    gpu_info=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
    echo "  📊 GPU: $gpu_info"
    memory=$(echo $gpu_info | cut -d',' -f2 | tr -d ' ')
    if [ "$memory" -lt 2048 ]; then
        echo "  ⚠️  Low GPU memory detected (<2GB) - Use LOW_MEMORY mode"
    else
        echo "  ✅ Sufficient GPU memory"
    fi
else
    echo "  ❌ NVIDIA drivers not found (CPU mode only)"
fi

echo ""

# Check disk space
echo "💾 Disk Space:"
available=$(df -h . | awk 'NR==2 {print $4}')
echo "  📦 Available space: $available"

echo ""

# Check required files
echo "📁 Required Files:"
files=("Dockerfile" "requirements.txt" "src/app.py" "src/performance_config.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file missing"
    fi
done

echo ""

# Check model files
echo "🤖 Model Files:"
if [ -d "models" ]; then
    echo "  ✅ Models directory exists"
    yolo_models=$(ls models/yolov11*-face.pt 2>/dev/null | wc -l)
    echo "  📊 YOLO models found: $yolo_models"
    if [ -d "models/antelopev2" ]; then
        echo "  ✅ InsightFace antelopev2 model directory exists"
    else
        echo "  ⚠️  InsightFace models will be downloaded on first run"
    fi
else
    echo "  ❌ Models directory missing"
fi

echo ""

# Network check
echo "🌐 Network Status:"
if curl -s http://localhost:8501/_stcore/health &> /dev/null; then
    echo "  ✅ App running and accessible at http://localhost:8501"
elif netstat -tulpn 2>/dev/null | grep :8501 &> /dev/null; then
    echo "  ⚠️  Port 8501 in use but health check failed"
else
    echo "  📱 Port 8501 available"
fi

echo ""
echo "🚀 Quick Commands:"
echo "  Build GPU version:  ./docker_build_fix.sh"
echo "  Build lite version: ./docker_test_lite.sh" 
echo "  Run simple:         ./docker_simple.sh"
echo "  Check logs:         docker logs CONTAINER_NAME"
echo "  Stop all:           docker stop \$(docker ps -q --filter 'publish=8501')"
echo ""
