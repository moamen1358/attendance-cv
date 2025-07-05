# Face Recognition System - GPU Setup

## Quick Start (GPU Required)

### Option 1: Simple Run Script
```bash
./run_gpu.sh
```

### Option 2: Docker Compose
```bash
docker compose up -d
```

### Option 3: Manual Docker Run
```bash
docker run -d --name face_recognition_app --gpus all -p 8501:8501 -v $(pwd):/app moamen1358/my_face_recognition_app:latest /app/start_gpu.sh
```

## Access
- **Web Interface:** http://localhost:8501
- **Container Name:** face_recognition_app

## Essential Files

### Core Files (DO NOT DELETE)
- `Dockerfile` - Container build configuration
- `docker-compose.yml` - GPU-enabled compose configuration  
- `start_gpu.sh` - GPU-optimized startup script with InsightFace patches
- `run_gpu.sh` - Simple runner for GPU container
- `src/` - Application source code
- `models/` - AI models (YOLO, InsightFace)
- `requirements.txt` - Python dependencies

### Configuration
- `src/performance_config.py` - GPU performance settings (MX250 optimized)

## Container Management

```bash
# View logs
docker logs face_recognition_app

# Stop container  
docker stop face_recognition_app

# Restart container
docker restart face_recognition_app

# Remove container
docker rm face_recognition_app

# Execute commands in container
docker exec -it face_recognition_app bash
```

## GPU Requirements
- NVIDIA GPU with CUDA support
- NVIDIA Docker runtime
- 2GB+ VRAM recommended

## Features
- Real-time face detection and recognition
- Attendance tracking system
- Student/teacher management
- Live camera processing
- Database operations
- Report generation

---
**Note:** This system is optimized for NVIDIA GeForce MX250 (2GB VRAM) but works with other NVIDIA GPUs.
