# Level 7 Feeders Contact Form - Production

A production-ready Flask application for collecting solemn declarations with OTP verification, MongoDB storage, and Redis session management.

## � Quick Deployment

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM available
- 10GB+ disk space

### Deploy in 3 Steps

1. **Configure Environment**
   ```bash
   copy .env.production.template .env.production
   # Edit .env.production with your settings
   ```

2. **Setup Data Directories**
   ```powershell
   .\setup-production-dirs.ps1
   ```

3. **Deploy**
   ```bash
   .\deploy-prod.sh deploy
   ```

## 📋 Features

- ✅ **OTP Verification** - SMS/Email verification system
- ✅ **MongoDB Storage** - Persistent document storage
- ✅ **Redis Sessions** - Fast session management
- ✅ **Health Monitoring** - Built-in health checks
- ✅ **Production Ready** - Gunicorn WSGI server
- ✅ **Configurable Storage** - Custom data paths
- ✅ **Greek Localization** - Fully localized interface

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx/LB      │    │  Flask App      │    │   MongoDB       │
│   (Optional)    │───▶│  (Gunicorn)     │───▶│   Database      │
│   Port 80/443   │    │  Port 5000      │    │   Port 27017    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   Sessions/OTP  │
                       │   Port 6379     │
                       └─────────────────┘
```

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_ROOT_PATH` | Root path for all data | `./production-data` |
| `MONGO_ROOT_PASSWORD` | MongoDB admin password | *Required* |
| `SMTP_USER` | Email sender | *Required* |
| `SMTP_PASS` | Email password | *Required* |

### Data Storage

All persistent data is stored in configurable directories:

```
production-data/
├── MongoDB/     # Database files
├── RedisData/   # Redis persistence
├── logs/        # Application logs
├── nginx/       # Nginx config (if used)
└── ssl/         # SSL certificates
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:5000/health
```

### Logs
```bash
docker logs L7SubmitForm_Prod --tail 50
```

### Container Status
```bash
docker ps
```

## 🔧 Management

### Start Services
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Stop Services
```bash
docker compose -f docker-compose.prod.yml down
```

### Update Application
```bash
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## 🔐 Security

- Non-root container execution
- Environment variable isolation
- Network segmentation
- Resource limits
- Input validation
- CSRF protection

## 📱 Usage

1. **Access Form**: http://localhost:5000
2. **Fill Details**: Name, phone, email, message
3. **OTP Verification**: Receive and enter OTP
4. **Submit**: Declaration saved to MongoDB

## 🚨 Troubleshooting

### Common Issues

**Container won't start:**
```bash
docker logs [container_name]
```

**Permission errors:**
```bash
# Windows
icacls "data-path" /grant "$env:USERNAME:(OI)(CI)F" /T

# Linux/macOS
chmod -R 755 /data-path
```

**MongoDB connection failed:**
- Check `MONGO_ROOT_PASSWORD` is set
- Verify network connectivity
- Check MongoDB logs

**Redis connection failed:**
- Verify Redis container is healthy
- Check network configuration

## 📚 Documentation

- [Storage Configuration](PRODUCTION-STORAGE.md)
- [Deployment Guide](deploy-prod.sh)
- [Environment Template](.env.production.template)

## 🏷️ Version

- **Application**: v2.0.1-production
- **Python**: 3.11
- **Flask**: 3.1.1
- **MongoDB**: 7.0
- **Redis**: Alpine

## 📧 Support

For production issues, check logs and health endpoints first. Ensure all environment variables are properly configured.

---

**Production Ready** ✅ | **Health Monitored** 📊 | **Secure** 🔐
