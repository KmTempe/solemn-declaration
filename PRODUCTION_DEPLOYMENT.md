# Production Deployment Guide

## 🚀 Level 7 Feeders Contact Form - Production Ready

### ✅ Pre-Deployment Checklist

**Application Status:**
- ✅ Redis Sessions: Fixed with binary Redis client
- ✅ MongoDB Integration: Complete with data persistence 
- ✅ Email Functionality: SMTP configured and tested
- ✅ OTP Verification: Working end-to-end
- ✅ Error Handling: Comprehensive with fallbacks
- ✅ Security: Session signing, rate limiting, input validation
- ✅ Monitoring: Metrics and logging implemented

## 📋 Production Deployment Steps

### 1. **Environment Configuration**

Create production `.env` file:
```bash
# Production Environment Variables
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
RECIPIENT_EMAIL=your-email@gmail.com
FLASK_SECRET=CHANGE_THIS_TO_A_RANDOM_64_CHAR_STRING
FLASK_ENV=production
FLASK_DEBUG=0
REDIS_URL=redis://redis:6379/0
MONGO_URL=mongodb://mongodb:27017/solemn_declarations

# Production-specific settings
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
```

### 2. **Security Hardening**

Update `docker-compose.yml` for production:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:5000"  # Production port
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    env_file:
      - .env
    depends_on:
      - redis
      - mongodb
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  redis:
    image: redis:alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:7.0
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
      MONGO_INITDB_DATABASE: solemn_declarations
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.runCommand('ping').ok"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
    driver: local
  mongodb_data:
    driver: local

networks:
  default:
    driver: bridge
```

### 3. **SSL/TLS Configuration**

For HTTPS deployment, add nginx reverse proxy:
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped
```

### 4. **Production Commands**

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl -f http://localhost/health

# Monitor logs
docker-compose logs -f web

# Backup database
docker exec mongodb mongodump --out /backup/$(date +%Y%m%d)

# Monitor metrics
curl http://localhost/metrics
```

### 5. **Monitoring & Maintenance**

```bash
# Production monitoring scripts
#!/bin/bash

# Health check script
check_health() {
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Application healthy"
    else
        echo "❌ Application unhealthy - restarting"
        docker-compose restart web
    fi
}

# Database backup
backup_db() {
    docker exec mongodb mongodump --out /backup/$(date +%Y%m%d_%H%M%S)
    echo "📦 Database backup completed"
}

# Log rotation
rotate_logs() {
    docker-compose logs --no-color > /var/log/level7-form.log
    docker-compose logs --no-color --tail=1000 > /var/log/level7-form-recent.log
}
```

## 🔒 Security Considerations

### Production Security Updates:

1. **Session Security:**
   ```python
   app.config.update({
       'SESSION_COOKIE_SECURE': True,  # HTTPS only
       'SESSION_COOKIE_HTTPONLY': True,
       'SESSION_COOKIE_SAMESITE': 'Strict',
   })
   ```

2. **Rate Limiting:**
   - Form submissions: 5 per hour per IP
   - OTP requests: 3 per hour per email
   - Email sending: Protected with exponential backoff

3. **Input Validation:**
   - Phone number validation with mobile-validate
   - Email format validation
   - XSS protection with template escaping
   - SQL injection prevention (using MongoDB ODM)

## 📊 Production Metrics

Available at `/metrics`:
- Form submission success rate
- OTP verification success rate  
- Email delivery success rate
- Response times
- Error rates
- Active sessions

## 🎯 Production Features

✅ **Scalability:**
- Redis sessions for multiple app instances
- MongoDB for persistent data storage
- Docker containers for easy scaling

✅ **Reliability:**
- Health checks for all services
- Automatic restarts on failure
- Data persistence with volumes
- Graceful error handling

✅ **Performance:**
- Redis caching for OTP and rate limiting
- Optimized database queries
- Connection pooling
- Resource limits

✅ **Security:**
- HTTPS enforcement (with nginx)
- Secure session configuration
- Rate limiting and CAPTCHA protection
- Input validation and sanitization

## 🚀 Deployment Commands

```bash
# 1. Final build
docker-compose build --no-cache

# 2. Deploy to production
docker-compose up -d

# 3. Verify deployment
./scripts/health-check.sh

# 4. Monitor initial traffic
docker-compose logs -f web | grep -E "(ERROR|SUCCESS|OTP)"
```

## 📞 Production Support

**Health Endpoints:**
- `/health` - Application health check
- `/metrics` - Prometheus-compatible metrics
- `/submissions` - View recent submissions (admin)

**Log Locations:**
- Application logs: `docker-compose logs web`
- Database logs: `docker-compose logs mongodb`
- Redis logs: `docker-compose logs redis`

---

## 🎉 Production Ready Checklist

- ✅ Redis sessions working with binary client
- ✅ Email functionality tested and working
- ✅ MongoDB data persistence operational
- ✅ OTP verification end-to-end tested
- ✅ Rate limiting and security measures active
- ✅ Health checks and monitoring implemented
- ✅ Error handling and fallbacks in place
- ✅ Production environment configuration ready

**The application is production-ready and fully operational! 🚀**
