# 🚀 Complete Deployment Guide

This guide covers multiple deployment options for the Face Recognition Attendance System.

## 📋 Prerequisites

- Docker installed
- Git (for cloning)
- At least 4GB RAM
- GPU support (optional but recommended)

## 🐳 Docker Deployment Options

### Option 1: Quick Test (No GPU)
```bash
# Build and run lightweight version
./docker_test_lite.sh
```

### Option 2: Full GPU-Enabled Build
```bash
# Build with CUDA support
./docker_build_fix.sh
```

### Option 3: Simple Docker Run
```bash
# Quick deployment
./docker_simple.sh
```

### Option 4: Docker Compose
```bash
# Full stack deployment
docker-compose up -d
```

## 🛠️ Build Scripts Explained

### `docker_build_fix.sh`
- Full CUDA-enabled build
- Fixes blinker package conflicts
- Optimized for production

### `docker_test_lite.sh`
- Lightweight Python-slim build
- Faster build times
- CPU-only (for testing)

### `docker_simple.sh`
- Simple build and run
- Good for development

## 📊 Performance Configuration

Edit `src/performance_config.py` to adjust:

```python
# Model Selection
INSIGHTFACE_MODEL = "antelopev2"  # or "buffalo_sc", "buffalo_l"
YOLO_MODEL_SIZE = "l"             # "n", "s", "m", "l", "x"

# Performance Settings
DETECTION_SIZE = (480, 480)       # Lower for faster processing
CONFIDENCE_THRESHOLD = 0.25       # Adjust detection sensitivity
GPU_MODE = "LOW_MEMORY"           # For GPUs with <2GB memory
```

## 🔧 Troubleshooting

### Build Issues

1. **Blinker conflicts**:
   ```bash
   # Already fixed in Dockerfile with:
   RUN apt-get remove -y python3-blinker || true
   RUN pip install "blinker>=1.6.2"
   ```

2. **CUDA not found**:
   ```bash
   # Use lite version for testing:
   ./docker_test_lite.sh
   ```

3. **Out of memory**:
   - Use `YOLO_MODEL_SIZE = "n"` (nano)
   - Reduce `DETECTION_SIZE` to (320, 320)
   - Set `GPU_MODE = "LOW_MEMORY"`

### Runtime Issues

1. **Port already in use**:
   ```bash
   docker stop $(docker ps -q --filter "publish=8501")
   ```

2. **Camera access**:
   ```bash
   # Add device access:
   docker run --device /dev/video0 -p 8501:8501 attendance-app
   ```

3. **Model files missing**:
   ```bash
   # Ensure models directory is copied:
   ls -la models/
   ```

## 📱 Access the App

Once running, access at:
- **Local**: http://localhost:8501
- **Network**: http://YOUR_IP:8501

## 🔍 Monitoring

```bash
# Check container status
docker ps

# View logs
docker logs CONTAINER_NAME

# Monitor resource usage
docker stats
```

## 🛡️ Security Notes

- Change default passwords in production
- Use HTTPS in production (certificates included)
- Limit network access as needed
- Regular security updates

## 📦 Model Management

Models are automatically downloaded on first run:
- InsightFace models: `models/antelopev2/`
- YOLO models: `models/yolov11*-face.pt`

## 🔄 Updates

To update the application:
```bash
git pull
./docker_build_fix.sh
```

## 💾 Data Persistence

Important directories to backup:
- `store/` - Face embeddings database
- `attendance_system.db` - Main database
- `data_frames/` - CSV exports

## 🌐 Cloud Deployment

For cloud deployment, consider:
- AWS ECS with GPU instances
- Google Cloud Run (CPU version)
- Azure Container Instances
- DigitalOcean App Platform

## 🤝 Support

For issues:
1. Check logs: `docker logs CONTAINER_NAME`
2. Verify configuration in `performance_config.py`
3. Try lite version first: `./docker_test_lite.sh`
4. Check system requirements
