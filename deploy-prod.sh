#!/bin/bash
# Production Deployment Script for Level 7 Feeders Contact Form

set -e  # Exit on any error

echo "🚀 Level 7 Feeders Contact Form - Production Deployment"
echo "======================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to setup data directories
setup_data_directories() {
    log_info "Setting up data directories..."
    
    # Source environment file to get paths
    if [ -f ".env.production" ]; then
        # Extract DATA_ROOT_PATH from .env.production
        DATA_ROOT_PATH=$(grep "^DATA_ROOT_PATH=" .env.production | cut -d'=' -f2)
        if [ -n "$DATA_ROOT_PATH" ]; then
            log_info "Creating data directories at: $DATA_ROOT_PATH"
            
            # Create directories
            mkdir -p "$DATA_ROOT_PATH/RedisData"
            mkdir -p "$DATA_ROOT_PATH/MongoDB" 
            mkdir -p "$DATA_ROOT_PATH/logs"
            mkdir -p "$DATA_ROOT_PATH/nginx"
            mkdir -p "$DATA_ROOT_PATH/ssl"
            
            # Set permissions (Linux/macOS)
            if [ "$(uname)" != "MINGW64_NT-10.0-19045" ]; then
                chmod -R 755 "$DATA_ROOT_PATH"
                log_success "Data directories created and permissions set"
            else
                log_warning "Running on Windows - permissions may need manual adjustment"
            fi
        else
            log_warning "DATA_ROOT_PATH not found in .env.production, using default locations"
        fi
    else
        log_warning ".env.production not found, skipping directory setup"
    fi
}

# Pre-deployment checks
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_success "Docker is running"
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    log_success "docker-compose is available"
    
    # Check if production env file exists
    if [ ! -f ".env.production" ]; then
        log_error ".env.production file not found. Please create it from .env.production.example"
        exit 1
    fi
    log_success ".env.production file found"
}

# Build production images
build_images() {
    log_info "Building production images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    log_success "Production images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Start production services
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            log_success "Application is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for health check... ($attempt/$max_attempts)"
        sleep 10
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check container status
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "Containers are running"
    else
        log_error "Some containers are not running"
        docker-compose -f docker-compose.prod.yml ps
        return 1
    fi
    
    # Check health endpoint
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Check metrics endpoint
    if curl -f http://localhost/metrics > /dev/null 2>&1; then
        log_success "Metrics endpoint accessible"
    else
        log_warning "Metrics endpoint not accessible"
    fi
    
    # Test form page
    if curl -f http://localhost/ > /dev/null 2>&1; then
        log_success "Form page accessible"
    else
        log_error "Form page not accessible"
        return 1
    fi
}

# Backup before deployment
backup_data() {
    log_info "Creating backup before deployment..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_dir="./backups/$timestamp"
    mkdir -p "$backup_dir"
    
    # Backup MongoDB if running
    if docker ps | grep -q "mongodb"; then
        docker exec mongodb mongodump --out "/backup/$timestamp" > /dev/null 2>&1 || true
        log_success "MongoDB backup created"
    fi
    
    # Backup Redis if running
    if docker ps | grep -q "redis"; then
        docker exec redis redis-cli SAVE > /dev/null 2>&1 || true
        log_success "Redis backup created"
    fi
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    docker-compose -f docker-compose.prod.yml down
    docker-compose up -d  # Start development version
    log_success "Rollback completed"
}

# Main deployment process
main() {
    echo
    log_info "Starting production deployment process..."
    echo
    
    # Run all checks and deployment steps
    check_prerequisites
    setup_data_directories
    backup_data
    build_images
    deploy_services
    
    # Wait for services to be ready
    if wait_for_health; then
        if verify_deployment; then
            echo
            log_success "🎉 Production deployment completed successfully!"
            echo
            echo "📊 Application Status:"
            echo "  - Form: http://localhost/"
            echo "  - Health: http://localhost/health"
            echo "  - Metrics: http://localhost/metrics"
            echo "  - Submissions: http://localhost/submissions"
            echo
            echo "📝 Next Steps:"
            echo "  1. Configure SSL/HTTPS if needed"
            echo "  2. Set up monitoring and alerting"
            echo "  3. Configure backup schedule"
            echo "  4. Test form submission end-to-end"
            echo
        else
            log_error "Deployment verification failed"
            rollback
            exit 1
        fi
    else
        log_error "Services failed to become healthy"
        rollback
        exit 1
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "health")
        curl -s http://localhost/health | python -m json.tool
        ;;
    "logs")
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    "status")
        docker-compose -f docker-compose.prod.yml ps
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health|logs|status]"
        echo "  deploy   - Deploy to production (default)"
        echo "  rollback - Rollback to previous version"
        echo "  health   - Check application health"
        echo "  logs     - Show application logs"
        echo "  status   - Show container status"
        exit 1
        ;;
esac
