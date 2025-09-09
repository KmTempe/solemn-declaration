# 🚀 Production Deployment with Custom Data Storage

## Overview
Your Level 7 Feeders Contact Form now supports fully customizable data storage paths for production deployment. This allows you to store container data wherever you prefer on your system.

## What's New ✨

### 1. Configurable Storage Paths
- **Redis Data**: Store Redis persistence files anywhere
- **MongoDB Data**: Choose your database storage location  
- **Application Logs**: Centralize log files
- **Nginx Config**: Custom configuration directory
- **SSL Certificates**: Secure certificate storage

### 2. Easy Setup
- PowerShell script for Windows directory creation
- Automated permission setting
- Template-based configuration
- Built-in validation

### 3. Production Ready
- Enhanced deployment script with directory setup
- Health checks for all services
- Automatic backup before deployment
- Rollback capability

## Quick Start Guide

### Step 1: Configure Storage Paths
```bash
# Copy the template
copy .env.production.template .env.production

# Edit .env.production and set your desired path:
DATA_ROOT_PATH=I:/forma/solemn-declaration/production-data
```

### Step 2: Create Directories
```powershell
# Windows PowerShell
.\setup-production-dirs.ps1

# This creates:
# - production-data/RedisData/
# - production-data/MongoDB/
# - production-data/logs/
# - production-data/nginx/
# - production-data/ssl/
```

### Step 3: Deploy
```bash
.\deploy-prod.sh deploy
```

## Example Configurations

### 🖥️ Windows Examples
```bash
# External drive
DATA_ROOT_PATH=E:/DockerData/level7-form

# Network storage
DATA_ROOT_PATH=//NAS-SERVER/docker/level7-form

# User profile
DATA_ROOT_PATH=C:/Users/admin/Documents/level7-data
```

### 🐧 Linux Examples
```bash
# System directory
DATA_ROOT_PATH=/var/lib/level7-form

# User home
DATA_ROOT_PATH=/home/user/docker-data/level7-form

# Mounted storage
DATA_ROOT_PATH=/mnt/storage/level7-form
```

## Directory Structure
```
production-data/
├── RedisData/          # Redis AOF & RDB files
├── MongoDB/            # MongoDB WiredTiger files
├── logs/               # Flask application logs
├── nginx/              # Nginx configuration
└── ssl/                # SSL certificates & keys
```

## Key Benefits

### 🔒 Security
- Data stored outside container filesystem
- Persistent across container updates
- Custom backup strategies possible

### 📊 Performance  
- Choose high-performance storage
- SSD optimization for databases
- Network storage support

### 🛠️ Management
- Centralized data location
- Easy backup and migration
- Clear data ownership

### 🔧 Flexibility
- Multiple deployment environments
- Development vs production separation
- Easy configuration management

## Migration from Previous Setup

If you're upgrading from a previous deployment:

1. **Stop containers**: `docker compose down`
2. **Backup existing data**: `docker volume ls` and copy data
3. **Configure new paths**: Edit `.env.production`
4. **Create directories**: Run setup script
5. **Copy data**: Move from old volumes to new directories
6. **Deploy**: `.\deploy-prod.sh deploy`

## Troubleshooting

### Permission Issues
```powershell
# Windows - run as Administrator
icacls "C:\path\to\data" /grant "$env:USERNAME:(OI)(CI)F" /T
```

### Path Not Found
- Verify directory exists
- Check path format (use forward slashes on Windows)
- Ensure no trailing slashes

### Container Start Failures
```bash
# Check container logs
docker logs L7MongoDB_Prod
docker logs L7Redis_Prod

# Verify volume mounts
docker inspect L7MongoDB_Prod | grep -A 10 "Mounts"
```

## Advanced Configuration

### Custom Redis Settings
Add to `.env.production`:
```bash
REDIS_MAXMEMORY=512mb
REDIS_SAVE_INTERVAL=300
```

### MongoDB Optimization
```bash
MONGO_CACHE_SIZE=256MB
MONGO_JOURNAL_COMMIT_INTERVAL=100
```

### Nginx SSL Setup
```bash
# Enable SSL profile
docker compose --profile ssl up -d nginx

# Certificate paths automatically configured:
# ${NGINX_SSL_PATH}/cert.pem
# ${NGINX_SSL_PATH}/private.key
```

## Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl http://localhost/health

# Individual services  
docker exec L7Redis_Prod redis-cli ping
docker exec L7MongoDB_Prod mongosh --eval "db.runCommand('ping')"
```

### Backup Strategy
```bash
# Automated backup (included in deploy script)
.\deploy-prod.sh backup

# Manual backup
tar -czf backup-$(date +%Y%m%d).tar.gz production-data/
```

### Log Management
```bash
# View application logs
docker logs L7SubmitForm_Prod --tail 100

# Application file logs
tail -f production-data/logs/app.log
```

## Support & Resources

- 📖 **Full Documentation**: `PRODUCTION-STORAGE.md`
- 🔧 **Setup Script**: `setup-production-dirs.ps1`
- 🚀 **Deployment**: `deploy-prod.sh`
- ⚙️ **Configuration**: `.env.production.template`

---

**Ready to deploy?** Your production environment now has enterprise-grade data management! 🎉
