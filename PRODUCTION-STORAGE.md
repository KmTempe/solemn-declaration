# Production Data Storage Configuration

This guide explains how to configure custom data storage paths for your Level 7 Feeders Contact Form production deployment.

## Overview

The production deployment now supports configurable data storage paths, allowing you to specify exactly where Docker containers should store their persistent data.

## Quick Start

### 1. Copy Environment Template
```bash
copy .env.production.template .env.production
```

### 2. Edit Data Paths
Open `.env.production` and customize the `DATA_ROOT_PATH`:

```bash
# Example paths for different operating systems:

# Windows (recommended format)
DATA_ROOT_PATH=I:/forma/solemn-declaration/production-data

# Windows (alternative format)
DATA_ROOT_PATH=C:\\Docker\\level7-form-data

# Linux
DATA_ROOT_PATH=/var/lib/level7-form-data

# macOS
DATA_ROOT_PATH=/Users/username/docker-data/level7-form
```

### 3. Create Directories

**On Windows (PowerShell):**
```powershell
.\setup-production-dirs.ps1 -DataRootPath "I:\forma\solemn-declaration\production-data"
```

**On Linux/macOS:**
```bash
mkdir -p /var/lib/level7-form-data/{RedisData,MongoDB,logs,nginx,ssl}
chmod -R 755 /var/lib/level7-form-data
```

### 4. Deploy
```bash
.\deploy-prod.sh deploy
```

## Directory Structure

After setup, your data directory will look like:

```
production-data/
├── RedisData/          # Redis persistence data
├── MongoDB/            # MongoDB database files  
├── logs/               # Application logs
├── nginx/              # Nginx configuration (if using SSL)
└── ssl/                # SSL certificates (if using HTTPS)
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATA_ROOT_PATH` | Base path for all data | `I:/forma/solemn-declaration/production-data` |
| `REDIS_DATA_PATH` | Redis data directory | `${DATA_ROOT_PATH}/RedisData` |
| `MONGODB_DATA_PATH` | MongoDB data directory | `${DATA_ROOT_PATH}/MongoDB` |
| `APP_LOGS_PATH` | Application logs | `${DATA_ROOT_PATH}/logs` |
| `NGINX_CONFIG_PATH` | Nginx config directory | `${DATA_ROOT_PATH}/nginx` |
| `NGINX_SSL_PATH` | SSL certificates | `${DATA_ROOT_PATH}/ssl` |

## Default Behavior

If you don't specify custom paths, the system will use:
- `./production-data/` relative to your project directory

## Path Format Guidelines

### Windows
- Use forward slashes: `C:/Docker/data`
- Or double backslashes: `C:\\Docker\\data`
- Avoid single backslashes in environment files

### Linux/macOS
- Use standard Unix paths: `/var/lib/app-data`
- Ensure the user has write permissions

## Security Considerations

1. **Permissions**: Ensure Docker has read/write access to your data directories
2. **Backup**: The data directories contain all persistent data - back them up regularly
3. **Space**: Monitor disk space in your data directory
4. **Network Storage**: Can be used with network-attached storage (NAS)

## Troubleshooting

### Permission Errors
```bash
# Linux/macOS - fix permissions
sudo chown -R $USER:$USER /path/to/data
chmod -R 755 /path/to/data

# Windows - run PowerShell as Administrator
icacls "C:\Docker\data" /grant "$env:USERNAME:(OI)(CI)F" /T
```

### Path Not Found
- Verify the directory exists
- Check path format (forward slashes on Windows)
- Ensure no trailing slashes

### Container Start Issues
- Check Docker logs: `docker logs L7MongoDB_Prod`
- Verify volume mounts: `docker inspect L7MongoDB_Prod`
- Test directory write permissions

## Migration from Previous Setup

If upgrading from the old volume-based setup:

1. Stop current containers: `docker compose down`
2. Copy data from old volumes to new directories
3. Update `.env.production` with new paths
4. Deploy with new configuration

## Examples

### Example 1: External Drive (Windows)
```bash
# .env.production
DATA_ROOT_PATH=E:/DockerData/level7-form
```

### Example 2: Network Storage (Linux)
```bash
# .env.production  
DATA_ROOT_PATH=/mnt/nas/docker/level7-form
```

### Example 3: User Home Directory (macOS)
```bash
# .env.production
DATA_ROOT_PATH=/Users/admin/Documents/level7-form-data
```

## Support

If you encounter issues:
1. Check the deployment logs
2. Verify directory permissions
3. Test with default paths first
4. Review Docker container logs
