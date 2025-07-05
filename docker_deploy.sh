#!/bin/bash

# Face Recognition App Docker Deployment Script
# Usage: ./docker_deploy.sh [build|run|stop|logs|clean]

set -e

IMAGE_NAME="moamen1358/my_face_recognition_app"
CONTAINER_NAME="face_recognition_app"
DOCKER_COMPOSE_CMD="docker-compose"  # Default, will be updated by check_requirements

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

check_requirements() {
    print_status "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose (both old and new syntax)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
        print_success "Docker Compose (standalone) found"
    elif docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
        print_success "Docker Compose (plugin) found"
    else
        print_error "Docker Compose is not installed or not available"
        exit 1
    fi
    
    # Check nvidia-docker (for GPU support)
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU detected"
        # Quick check for Docker GPU support without hanging
        if docker info 2>/dev/null | grep -q nvidia; then
            print_success "GPU support available in Docker"
        else
            print_warning "GPU support may not be configured in Docker"
        fi
    else
        print_warning "No NVIDIA GPU detected, will run CPU-only"
    fi
    
    # Check required files
    required_files=("Dockerfile" "docker-compose.yml" "requirements.txt" "src/login.py")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Required file not found: $file"
            exit 1
        fi
    done
    
    print_success "All requirements satisfied"
}

build_image() {
    print_status "Building Docker image..."
    $DOCKER_COMPOSE_CMD build --no-cache
    print_success "Image built successfully"
}

run_container() {
    print_status "Starting container..."
    $DOCKER_COMPOSE_CMD up -d
    
    print_status "Waiting for container to be ready..."
    sleep 10
    
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        print_success "Container started successfully!"
        print_status "App should be available at: http://localhost:8501"
        print_status "Check logs with: ./docker_deploy.sh logs"
    else
        print_error "Container failed to start"
        $DOCKER_COMPOSE_CMD logs
        exit 1
    fi
}

stop_container() {
    print_status "Stopping container..."
    $DOCKER_COMPOSE_CMD down
    print_success "Container stopped"
}

show_logs() {
    print_status "Showing container logs..."
    $DOCKER_COMPOSE_CMD logs -f
}

clean_docker() {
    print_status "Cleaning up Docker resources..."
    $DOCKER_COMPOSE_CMD down --volumes --remove-orphans
    docker image prune -f
    docker volume prune -f
    print_success "Cleanup completed"
}

show_help() {
    echo "Face Recognition App Docker Deployment"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the Docker image"
    echo "  run       Start the application"
    echo "  stop      Stop the application"
    echo "  logs      Show application logs"
    echo "  restart   Stop and start the application"
    echo "  clean     Clean up Docker resources"
    echo "  check     Check system requirements"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run    # Build and run"
    echo "  $0 logs               # Show logs"
    echo "  $0 restart            # Restart app"
}

# Main script logic
case "${1:-help}" in
    "build")
        check_requirements
        build_image
        ;;
    "run")
        check_requirements
        run_container
        ;;
    "stop")
        stop_container
        ;;
    "logs")
        show_logs
        ;;
    "restart")
        print_status "Restarting application..."
        stop_container
        run_container
        ;;
    "clean")
        clean_docker
        ;;
    "check")
        check_requirements
        ;;
    "help"|*)
        show_help
        ;;
esac
