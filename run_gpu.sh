#!/bin/bash
# Simple GPU-enabled Face Recognition System Runner

echo "🚀 Starting Face Recognition System with GPU support..."

# Stop any existing container
docker stop face_recognition_app 2>/dev/null || true
docker rm face_recognition_app 2>/dev/null || true

# Run with GPU support
docker run -d \
  --name face_recognition_app \
  --gpus all \
  -p 8501:8501 \
  -v $(pwd):/app \
  moamen1358/my_face_recognition_app:latest \
  /app/start_gpu.sh

echo "✅ Container started!"
echo "📱 Access your app at: http://localhost:8501"
echo "📋 Container name: face_recognition_app"
echo ""
echo "Useful commands:"
echo "  View logs: docker logs face_recognition_app"
echo "  Stop:      docker stop face_recognition_app"
echo "  Restart:   docker restart face_recognition_app"
