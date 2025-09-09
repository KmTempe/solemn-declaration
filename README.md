# Solemn Declaration Form System

A Flask web application for collecting and managing solemn declarations with secure authentication and data validation.

## Overview

This system provides a web interface for users to submit solemn declarations with verification, data validation, and administrative oversight.

## Features

**Security**
- bcrypt password hashing with salt
- Redis-backed secure sessions
- Server-side validation and sanitization
- Environment-based secrets management

**Form Management**
- Structured form collection
- Real-time validation
- Document attachment support
- Greek localization

**Data Storage**
- MongoDB document storage
- Redis session caching
- JSON fallback storage
- Data migration tools

**Administration**
- Web-based admin interface
- Data export capabilities
- Submission tracking

**Production Ready**
- Docker containerization
- Health monitoring
- Performance optimization

## System Architecture

```
Web Browser → Flask App → MongoDB
(Users)       (Python)   (Database)
Port 80/443   Port 5000  Port 27017
                  ↓
              Redis Cache
              (Sessions)
              Port 6379
```

## Technology Stack

- Backend: Flask 3.x (Python)
- Database: MongoDB 7.x
- Cache: Redis 7.x
- Security: bcrypt, Flask-Session
- Frontend: HTML5, CSS3, JavaScript
- Deployment: Docker, Docker Compose

## Project Structure

```
solemn-declaration/
├── app.py                    # Main Flask application
├── mongo_helper.py           # MongoDB integration
├── redis_helper.py           # Redis cache and sessions
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.prod.yml  # Production deployment
├── docker-compose.dev.yml   # Development deployment
├── deploy-prod.ps1          # Production deployment script
├── deploy-dev.ps1           # Development deployment script
├── templates/               # HTML templates
├── static/                  # CSS, JS, images
└── .env.production          # Environment configuration
```

## Quick Start

1. See [Docker-Setup.md](Docker-Setup.md) for deployment instructions
2. Copy `.env.production.template` to `.env.production` and configure
3. Run `.\deploy-prod.ps1` for production or `.\deploy-dev.ps1` for development

## Configuration

All configuration is managed through environment variables in `.env.production`:

- Security: Admin credentials, Flask secrets
- Database: MongoDB and Redis connection strings
- Email: SMTP configuration for notifications
- Storage: Data persistence paths

## Health Monitoring

- `/health` - Application health check endpoint
- Application logs stored in `production-data/logs/`
- Error tracking and performance monitoring

## Docker Hub

The application is published as `kmtempe/solemn-declaration:latest` on Docker Hub.

```bash
# Pull and run
docker pull kmtempe/solemn-declaration:latest
docker run -p 5000:5000 kmtempe/solemn-declaration:latest
```

## Security Features

- bcrypt password hashing with salt
- Secure, HTTP-only cookies
- Server-side validation and sanitization
- Environment-based secrets management
- Authenticated database connections

## License

This project is open source software.

## Support

For technical support: Configure RECIPIENT_EMAIL in your environment

Version: 2.0.4
Last Updated: September 2025
Status: Production Ready
