# Solemn Declaration Form System

A production-ready Flask web application for collecting and managing solemn declarations with secure authentication, data validation, and persistent storage.

## 🎯 Project Overview

This system provides a secure web interface for users to submit solemn declarations with built-in verification, data validation, and administrative oversight. Designed for production environments with enterprise-grade security and scalability.

## ✨ Key Features

### 🔐 **Security First**
- **Secure Authentication** - bcrypt password hashing with salt
- **Session Management** - Redis-backed secure sessions
- **Input Validation** - Server-side validation and sanitization
- **Environment Security** - Secrets management via environment variables

### 📝 **Form Management**
- **Solemn Declarations** - Structured form collection
- **Data Validation** - Real-time client and server validation
- **File Uploads** - Secure document attachment support
- **Multi-language Support** - Greek localization included

### 🗄️ **Data Storage**
- **MongoDB Integration** - Document-based data persistence
- **Redis Caching** - Fast session and data caching
- **JSON Fallback** - Automatic fallback storage mechanism
- **Data Migration** - Built-in migration tools

### 👨‍💼 **Administration**
- **Admin Dashboard** - Web-based administration interface
- **Data Export** - CSV/JSON export capabilities
- **System Monitoring** - Health checks and metrics
- **User Management** - Submission tracking and management

### 🚀 **Production Ready**
- **Docker Support** - Full containerization with Docker Compose
- **Scalable Architecture** - Microservices-ready design
- **Health Monitoring** - Built-in health check endpoints
- **Performance Optimized** - Redis caching and optimized queries

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask App     │    │   MongoDB       │
│   (Users)       │───▶│   (Python)      │───▶│   (Database)    │
│   Port 80/443   │    │   Port 5000     │    │   Port 27017    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   (Sessions)    │
                       │   Port 6379     │
                       └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Flask 3.x (Python)
- **Database**: MongoDB 7.x
- **Cache**: Redis 7.x
- **Security**: bcrypt, Flask-Session
- **Frontend**: HTML5, CSS3, JavaScript
- **Deployment**: Docker, Docker Compose
- **Environment**: Production-ready configuration

## 📦 Project Structure

```
solemn-declaration/
├── app.py                 # Main Flask application
├── mongo_helper.py        # MongoDB integration
├── redis_helper.py        # Redis cache and sessions
├── redis_session_simple.py # Session management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.prod.yml # Production deployment
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── production-data/      # Data persistence
└── .env.production       # Environment configuration
```

## 🚀 Quick Start

1. **See Docker Setup** → [Docker-Setup.md](Docker-Setup.md)
2. **Understand Architecture** → [Documentation.md](Documentation.md)
3. **Configure Environment** → Copy `.env.production.template` to `.env.production`

## 🔧 Configuration

### Environment Variables
All configuration is managed through environment variables in `.env.production`:

- **Security**: Admin credentials, Flask secrets
- **Database**: MongoDB and Redis connection strings
- **Email**: SMTP configuration for notifications
- **Storage**: Data persistence paths

### Admin Access
- **Username**: Configured via `ADMIN_USERNAME`
- **Password**: Set via `ADMIN_PASSWORD` (automatically hashed with bcrypt)
- **Dashboard**: Available at `/admin` endpoint

## 📊 Monitoring & Health

### Health Endpoints
- `/health` - Basic application health
- `/health/detailed` - Comprehensive system status
- `/admin/metrics` - Administrative metrics and statistics

### Logging
- Application logs stored in `production-data/logs/`
- Error tracking and performance monitoring
- Configurable log levels and rotation

## 🔒 Security Features

- **Password Security**: bcrypt hashing with salt
- **Session Security**: Secure, HTTP-only cookies
- **Input Validation**: Server-side validation and sanitization
- **Environment Security**: Secrets stored in environment variables
- **Database Security**: Authenticated MongoDB connections

## 📝 License

This project is proprietary software developed for Level 7 Feeders.

## 🤝 Support

For technical support or questions:
- **Email**: level7feeders@gmail.com
- **Repository**: Private repository - access restricted

---

**Version**: 1.0.0  
**Last Updated**: September 2025  
**Status**: Production Ready ✅
