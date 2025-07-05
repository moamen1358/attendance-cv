#!/bin/bash

# Simple Docker deployment script (with build fixes)
# Usage: ./docker_simple.sh [build|run|stop|logs]

DOCKER_COMPOSE_CMD="docker compose"

case "${1:-help}" in
    "build")
        echo "🔨 Building Docker image (with fixes)..."
        docker system prune -f 2>/dev/null || true
        $DOCKER_COMPOSE_CMD build --no-cache
        echo "✅ Build complete!"
        ;;
    "run")
        echo "🚀 Starting application..."
        $DOCKER_COMPOSE_CMD up -d
        echo "✅ App started! Visit http://localhost:8501"
        ;;
    "stop")
        echo "🛑 Stopping application..."
        $DOCKER_COMPOSE_CMD down
        echo "✅ Stopped!"
        ;;
    "logs")
        echo "📋 Showing logs..."
        $DOCKER_COMPOSE_CMD logs -f
        ;;
    "restart")
        echo "🔄 Restarting..."
        $DOCKER_COMPOSE_CMD down
        $DOCKER_COMPOSE_CMD up -d
        echo "✅ Restarted!"
        ;;
    "clean")
        echo "🗑️ Cleaning up..."
        $DOCKER_COMPOSE_CMD down --volumes --remove-orphans
        docker system prune -af
        echo "✅ Cleaned!"
        ;;
    *)
        echo "Usage: $0 [build|run|stop|logs|restart|clean]"
        echo ""
        echo "Quick commands:"
        echo "  $0 build     # Build the image (with fixes)"
        echo "  $0 run       # Start the app"
        echo "  $0 logs      # Show logs"
        echo "  $0 stop      # Stop the app"
        echo "  $0 clean     # Clean everything"
        echo ""
        echo "For build issues, try: ./docker_build_fix.sh"
        ;;
esac
