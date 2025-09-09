# Docker Setup Guide

Complete guide for deploying the Solemn Declaration Form System using Docker for both development and production environments.

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **RAM**: 4GB+ available memory
- **Storage**: 10GB+ free disk space
- **Docker**: Docker Desktop 4.0+ or Docker Engine 20.10+
- **Docker Compose**: v2.0+

### Verify Docker Installation
```bash
docker --version
docker-compose --version
```

## 🚀 Docker Image Information

### Production Image
The application is published on Docker Hub as:
- **Repository**: `kmtempe/solemn-declaration`
- **Tags**: 
  - `latest` - Always points to the most recent version
  - `v2.0.4` - Specific version tag
- **Base Image**: `python:3.12-alpine3.20` (latest secure Alpine)
- **Size**: ~907MB (optimized with multi-stage build)
- **Security**: Non-root user, minimal dependencies, health checks

### Pull the Image
```bash
# Pull latest version
docker pull kmtempe/solemn-declaration:latest

# Pull specific version
docker pull kmtempe/solemn-declaration:v2.0.4
```

## 🔧 Development vs Production

This project provides two deployment configurations:

### Development Environment (`docker-compose.dev.yml`)
- **Purpose**: Local development with hot reload
- **Image**: Builds locally from Dockerfile
- **Features**: 
  - Source code mounted for live changes
  - Development environment variables
  - Debug mode enabled
- **Usage**: `.\deploy-dev.ps1`

### Production Environment (`docker-compose.prod.yml`)
- **Purpose**: Production deployment with pre-built images
- **Image**: Pulls from Docker Hub (`kmtempe/solemn-declaration:latest`)
- **Features**: 
  - Optimized for performance
  - Production environment variables
  - No source code mounting
- **Usage**: `.\deploy-prod.ps1`

## 🚀 Quick Deployment

### Development Deployment

1. **Environment Configuration**
```bash
# Copy template
copy .env.production.template .env.production

# Edit with your settings (Windows)
notepad .env.production
```

2. **Deploy Development Environment**
```powershell
# Windows PowerShell
.\deploy-dev.ps1

# Or manually
docker-compose -f docker-compose.dev.yml up -d
```

### Production Deployment

1. **Environment Configuration**
```bash
# Copy template
copy .env.production.template .env.production

# Edit with your production settings
notepad .env.production
```

2. **Setup Data Directories**

**Windows (PowerShell)**:
```powershell
.\setup-production-dirs.ps1
```

**Linux/Mac**:
```bash
mkdir -p production-data/{RedisData,MongoDB,logs,nginx,ssl}
chmod -R 755 production-data/
```

3. **Deploy Production Environment**

**Windows PowerShell**:
```powershell
.\deploy-prod.ps1
```

**Manual Deployment**:
```bash
# Pull latest images and start services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## 🛠️ Deployment Scripts

### Development Script (`deploy-dev.ps1`)
```powershell
# Deploy development environment
.\deploy-dev.ps1

# Other commands
.\deploy-dev.ps1 stop      # Stop all services
.\deploy-dev.ps1 logs      # View logs
.\deploy-dev.ps1 status    # Check status
.\deploy-dev.ps1 help      # Show help
```

### Production Script (`deploy-prod.ps1`)
```powershell
# Deploy production environment
.\deploy-prod.ps1

# Other commands
.\deploy-prod.ps1 stop      # Stop all services
.\deploy-prod.ps1 logs      # View logs
.\deploy-prod.ps1 status    # Check status
.\deploy-prod.ps1 help      # Show help
```

### Key Differences
- **Development**: Builds images locally, enables hot reload, debug mode
- **Production**: Uses pre-built Docker Hub images, optimized for performance

## ⚙️ Configuration Details

### Environment Variables (.env.production)

#### Flask Configuration
```bash
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_SECRET=your-secret-key-here
```

#### Admin Authentication
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password-here
```

#### Database Configuration
```bash
# Redis
REDIS_URL=redis://redis:6379/0

# MongoDB
MONGO_URL=mongodb://admin:password@mongodb:27017/solemn_declarations?authSource=admin
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-mongo-password
```

#### Data Storage Paths
```bash
DATA_ROOT_PATH=I:/forma/solemn-declaration/production-data
REDIS_DATA_PATH=${DATA_ROOT_PATH}/RedisData
MONGODB_DATA_PATH=${DATA_ROOT_PATH}/MongoDB
APP_LOGS_PATH=${DATA_ROOT_PATH}/logs
```

## 📦 Docker Images

### Development Image (Local Build)
- **Source**: Built from local Dockerfile
- **Purpose**: Development with live code changes
- **Features**:
  - Source code mounted as volumes
  - Hot reload enabled
  - Debug mode active
  - Development environment variables

### Production Image (Docker Hub)
- **Repository**: `kmtempe/solemn-declaration:latest`
- **Source**: Pre-built and published to Docker Hub
- **Purpose**: Production deployment
- **Features**:
  - Optimized and secure
  - No source code mounting
  - Production environment variables
  - Multi-stage build for smaller size

### Image Configuration

#### Base Image Features
- **Base**: `python:3.12-alpine3.20`
- **Security**: Non-root user (appuser)
- **Health Checks**: Built-in health monitoring
- **Optimization**: Minimal dependencies, cached layers
- **Logging**: Structured logging to `/app/logs`

#### Environment Differences
| Feature | Development | Production |
|---------|-------------|------------|
| Image Source | Local build | Docker Hub |
| Code Mounting | Yes (hot reload) | No |
| Debug Mode | Enabled | Disabled |
| SSL/TLS | Optional | Recommended |
| Resource Limits | Relaxed | Strict |

## 🏗️ Docker Services

### Application Stack
The Docker setup includes three main services:

#### 1. Flask Application (`app`)
- **Image**: Built from local Dockerfile
- **Port**: 5000 (internal)
- **Dependencies**: Redis, MongoDB
- **Health Check**: `/health` endpoint

#### 2. Redis Cache (`redis`)
- **Image**: redis:7-alpine
- **Port**: 6379 (internal)
- **Purpose**: Session storage, caching
- **Persistence**: Volume mounted to `RedisData/`

#### 3. MongoDB Database (`mongodb`)
- **Image**: mongo:7
- **Port**: 27017 (internal)
- **Purpose**: Document storage
- **Persistence**: Volume mounted to `MongoDB/`

### Network Configuration
All services run in an isolated Docker network with internal communication.

## 🔧 Docker Commands

### Service Management
```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart app

# View logs
docker-compose -f docker-compose.prod.yml logs -f [service]

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### Container Management
```bash
# Access application container
docker exec -it solemn-declaration-app bash

# Access MongoDB container
docker exec -it solemn-declaration-mongodb mongosh

# Access Redis container
docker exec -it solemn-declaration-redis redis-cli
```

### Volume Management
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect solemn-declaration_mongodb_data

# Backup MongoDB data
docker run --rm -v solemn-declaration_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz -C /data .
```

## 🔍 Monitoring & Debugging

### Health Checks
```bash
# Application health
curl http://localhost:5000/health

# Detailed health
curl http://localhost:5000/health/detailed

# Admin metrics (requires auth)
curl -u admin:password http://localhost:5000/admin/metrics
```

### Log Analysis
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs app

# Database logs
docker-compose -f docker-compose.prod.yml logs mongodb

# Cache logs
docker-compose -f docker-compose.prod.yml logs redis

# Follow logs in real-time
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Resource Monitoring
```bash
# Container resource usage
docker stats

# Specific container stats
docker stats solemn-declaration-app

# System resource usage
docker system df
```

## 🛠️ Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs [service]

# Verify environment file
cat .env.production

# Check port conflicts
netstat -tulpn | grep :5000
```

#### Database Connection Issues
```bash
# Test MongoDB connection
docker exec -it solemn-declaration-mongodb mongosh --eval "db.runCommand('ping')"

# Test Redis connection
docker exec -it solemn-declaration-redis redis-cli ping

# Check network connectivity
docker network ls
docker network inspect solemn-declaration_default
```

#### Permission Issues
```bash
# Fix data directory permissions (Linux/Mac)
sudo chown -R 999:999 production-data/MongoDB/
sudo chown -R 999:999 production-data/RedisData/

# Windows: Ensure Docker Desktop has access to the drive
```

### Performance Optimization

#### Memory Optimization
```yaml
# In docker-compose.prod.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

#### Storage Optimization
```bash
# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Clean system
docker system prune -a
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database Maintenance
```bash
# MongoDB backup
docker exec solemn-declaration-mongodb mongodump --out /backup

# Redis backup
docker exec solemn-declaration-redis redis-cli BGSAVE
```

### Security Updates
```bash
# Update base images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Production Considerations

### Scaling
- Use Docker Swarm or Kubernetes for multi-node deployment
- Implement load balancing with Nginx or HAProxy
- Consider external Redis/MongoDB services for high availability

### Security
- Use Docker secrets for sensitive data
- Implement network segmentation
- Regular security scanning with `docker scan`

### Monitoring
- Integrate with monitoring solutions (Prometheus, Grafana)
- Set up log aggregation (ELK stack)
- Configure alerting for critical issues

---

**Next Steps**: After deployment, see [Documentation.md](Documentation.md) for architecture details and component information.
