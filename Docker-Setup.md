# Docker Setup Guide

Complete guide for deploying the Solemn Declaration Form System using Docker in production environments.

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

## 🚀 Quick Deployment (Production)

### 1. Environment Configuration

Copy the environment template and configure for production:

```bash
# Copy template
copy .env.production.template .env.production

# Edit with your settings (Windows)
notepad .env.production

# Edit with your settings (Linux/Mac)
nano .env.production
```

### 2. Setup Data Directories

**Windows (PowerShell)**:
```powershell
.\setup-production-dirs.ps1
```

**Linux/Mac**:
```bash
mkdir -p production-data/{RedisData,MongoDB,logs,nginx,ssl}
chmod -R 755 production-data/
```

### 3. Deploy Application

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

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
