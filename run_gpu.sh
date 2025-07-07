#!/bin/bash
# Simple GPU-enabled Face Recognition System Runner

echo "🚀 Starting Face Recognition System with GPU support..."

# Stop any existing container
docker stop app 2>/dev/null || true
docker rm app 2>/dev/null || true

# Run with GPU support
docker run -d \
  --name app \
  --gpus all \
  -p 8501:8501 \
  -v $(pwd):/app \
  app:latest \
  /app/start_gpu.sh

echo "✅ Container started!"
echo "📱 Access your app at: http://localhost:8501"
echo "📋 Container name: app"
echo ""
echo "Useful commands:"
echo "  View logs: docker logs app"
echo "  Stop:      docker stop app"
echo "  Restart:   docker restart app"
