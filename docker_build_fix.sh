#!/bin/bash

# Docker Build Fix Script
# Handles common build issues including blinker conflict

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "🔧 Docker Build Fix Script"
echo "================================"

# Clean up existing containers and images
print_status "🗑️ Cleaning up existing Docker resources..."
docker compose down --remove-orphans 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# Check available disk space
available_space=$(df . | tail -1 | awk '{print $4}')
if [ "$available_space" -lt 10000000 ]; then
    print_warning "Low disk space detected. Consider freeing up space."
fi

# Build with no cache to ensure clean build
print_status "🔨 Building Docker image (no cache)..."
if docker build --no-cache -t moamen1358/my_face_recognition_app . 2>&1 | tee build.log; then
    print_success "✅ Docker build successful!"
    
    # Start the application
    print_status "🚀 Starting application..."
    if docker compose up -d; then
        print_success "✅ App started successfully!"
        echo ""
        echo "🌐 Access your app at: http://localhost:8501"
        echo "📋 Check logs with: docker compose logs -f"
        echo "🛑 Stop with: docker compose down"
    else
        print_error "❌ Failed to start application"
        docker compose logs
    fi
else
    print_error "❌ Docker build failed!"
    echo ""
    print_status "📋 Build error analysis:"
    
    # Check for common errors
    if grep -q "blinker" build.log; then
        print_error "🔍 Blinker conflict detected"
        echo "  Solution: The Dockerfile should handle this automatically now"
    fi
    
    if grep -q "CUDA" build.log; then
        print_warning "🔍 CUDA-related issue detected"
        echo "  This might be normal if no GPU is available"
    fi
    
    if grep -q "timeout" build.log; then
        print_warning "🔍 Network timeout detected"
        echo "  Solution: Check internet connection and try again"
    fi
    
    if grep -q "No space left" build.log; then
        print_error "🔍 Disk space issue detected"
        echo "  Solution: Free up disk space and try again"
    fi
    
    echo ""
    print_status "📋 Last 20 lines of build log:"
    tail -20 build.log
    
    echo ""
    print_status "🔧 Suggested next steps:"
    echo "1. Check internet connection"
    echo "2. Free up disk space if needed"
    echo "3. Try: docker system prune -af"
    echo "4. Retry this script"
fi

# Clean up build log
rm -f build.log 2>/dev/null || true
