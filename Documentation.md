# System Documentation

Comprehensive documentation covering the core components, architecture, and technical implementation of the Solemn Declaration Form System.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Client    │    │ Flask App   │    │  MongoDB    │    │
│  │  Browser    │───▶│ (Gunicorn)  │───▶│  Database   │    │
│  │             │    │ Port 5000   │    │ Port 27017  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                             │                              │
│                             ▼                              │
│                    ┌─────────────┐                        │
│                    │ Redis Cache │                        │
│                    │ (Sessions)  │                        │
│                    │ Port 6379   │                        │
│                    └─────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request → Flask Router → Authentication → Business Logic → Data Layer → Response
     ↑                                              ↓
     └── Session Management ← Redis Cache ←─────────┘
                                  ↓
                            MongoDB Storage
```

## 🧩 Core Components

### 1. Flask Application (`app.py`)

**Purpose**: Main application server and request handler

**Key Responsibilities**:
- HTTP request routing and handling
- User authentication and session management
- Form processing and validation
- Admin interface and dashboard
- Health monitoring and metrics

**Key Functions**:
```python
# Authentication
get_or_create_admin_hash()    # Secure password management
require_admin_auth()          # Authentication decorator

# Form Processing
submit_declaration()          # Main form submission
validate_form_data()          # Server-side validation

# Admin Functions
admin_dashboard()             # Administrative interface
export_data()                # Data export functionality
```

**Security Features**:
- bcrypt password hashing with salt
- Session-based authentication
- Input validation and sanitization
- Environment-based configuration

### 2. MongoDB Helper (`mongo_helper.py`)

**Purpose**: Database abstraction and MongoDB operations

**Key Responsibilities**:
- Database connection management
- Document CRUD operations
- Data validation and schema enforcement
- Migration utilities
- Connection health monitoring

**Core Classes**:
```python
class MongoHelper:
    def __init__()              # Connection initialization
    def is_available()          # Health check
    def save_submission()       # Store form data
    def get_submissions()       # Retrieve data
    def update_submission()     # Modify records
    def delete_submission()     # Remove records
```

**Database Schema**:
- **Collections**: `submissions`, `admin_config`, `system_metrics`
- **Indexes**: Optimized for common queries
- **Validation**: JSON schema validation
- **Backup**: Automated backup strategies

### 3. Redis Helper (`redis_helper.py`)

**Purpose**: Caching layer and performance optimization

**Key Responsibilities**:
- Session data storage
- Application caching
- Rate limiting
- Metrics tracking
- Health monitoring

**Core Functions**:
```python
class RedisHelper:
    def get()                   # Retrieve cached data
    def set()                   # Store data with TTL
    def delete()                # Remove cached items
    def cache_result()          # Decorator for caching
    def rate_limit()            # Rate limiting decorator
    def track_metric()          # Performance metrics
```

**Caching Strategy**:
- **Session Data**: User sessions with TTL
- **Form Data**: Temporary form storage
- **Metrics**: Application performance data
- **Rate Limiting**: Request throttling

### 4. Session Management (`redis_session_simple.py`)

**Purpose**: Secure session handling with Redis backend

**Key Responsibilities**:
- Session creation and destruction
- Session data serialization
- Security enforcement
- Session timeout management

**Session Security**:
- Secure session keys
- HTTP-only cookies
- SameSite protection
- Session timeout enforcement

## 🗄️ Data Architecture

### Database Design

#### MongoDB Collections

**1. Submissions Collection**
```javascript
{
  "_id": ObjectId,
  "submission_id": "unique_identifier",
  "timestamp": ISODate,
  "form_data": {
    "name": "string",
    "email": "string",
    "declaration": "text",
    "attachments": ["file_paths"]
  },
  "status": "pending|approved|rejected",
  "admin_notes": "string",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**2. Admin Config Collection**
```javascript
{
  "_id": ObjectId,
  "type": "admin_auth|system_settings",
  "password_hash": "bcrypt_hash",
  "settings": {
    "max_submissions_per_day": number,
    "email_notifications": boolean
  },
  "updated_at": ISODate
}
```

**3. System Metrics Collection**
```javascript
{
  "_id": ObjectId,
  "metric_type": "performance|usage|error",
  "value": number,
  "timestamp": ISODate,
  "metadata": {}
}
```

### Redis Data Structure

**Session Storage**:
```
session:{session_id} → {
  "user_id": "string",
  "authenticated": boolean,
  "csrf_token": "string",
  "last_activity": timestamp
}
```

**Cache Storage**:
```
cache:{key} → {
  "data": any,
  "ttl": seconds,
  "created_at": timestamp
}
```

**Metrics Storage**:
```
metrics:{type}:{date} → {
  "count": number,
  "avg_response_time": number,
  "errors": number
}
```

## 🔐 Security Architecture

### Authentication Flow

```
1. User Login Request
   ↓
2. Credential Validation (bcrypt)
   ↓
3. Session Creation (Redis)
   ↓
4. Secure Cookie Set
   ↓
5. Authenticated Access
```

### Security Layers

**1. Input Validation**
- Server-side form validation
- SQL injection prevention
- XSS protection
- File upload security

**2. Authentication Security**
- bcrypt password hashing
- Session-based authentication
- Secure cookie configuration
- Session timeout enforcement

**3. Network Security**
- Internal Docker networking
- Environment variable security
- Database authentication
- TLS/SSL support ready

**4. Data Security**
- Encrypted password storage
- Secure session management
- Data validation and sanitization
- Audit logging

## 🎛️ Configuration Management

### Environment Configuration

**Security Settings**:
```bash
FLASK_SECRET=crypto_secure_key
ADMIN_USERNAME=admin_user
ADMIN_PASSWORD=secure_password
```

**Database Configuration**:
```bash
MONGO_URL=mongodb://user:pass@host:port/db
REDIS_URL=redis://host:port/db
```

**Application Settings**:
```bash
FLASK_ENV=production
FLASK_DEBUG=false
SESSION_COOKIE_SECURE=true
```

### Configuration Hierarchy

1. **Environment Variables** (Highest Priority)
2. **Configuration Files** (.env.production)
3. **Default Values** (Fallback)

## 📊 Monitoring & Observability

### Health Check System

**Basic Health Check** (`/health`):
```python
{
  "status": "healthy",
  "timestamp": "2025-09-09T10:00:00Z",
  "uptime": "24h 30m"
}
```

**Detailed Health Check** (`/health/detailed`):
```python
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "cache": "connected",
    "disk_space": "85% available"
  },
  "metrics": {
    "requests_per_minute": 150,
    "avg_response_time": "120ms",
    "error_rate": "0.1%"
  }
}
```

### Metrics Collection

**Performance Metrics**:
- Request response times
- Database query performance
- Cache hit/miss ratios
- Memory and CPU usage

**Business Metrics**:
- Form submission rates
- User engagement metrics
- Error frequencies
- System availability

### Logging Strategy

**Log Levels**:
- `ERROR`: System errors and exceptions
- `WARNING`: Performance issues and deprecations
- `INFO`: Business logic events
- `DEBUG`: Detailed execution flow

**Log Format**:
```
[TIMESTAMP] [LEVEL] [MODULE] MESSAGE {context_data}
```

## 🔧 Development Guidelines

### Code Organization

```
app.py                     # Main application
├── Authentication        # User auth and session management
├── Form Processing        # Data validation and processing
├── Admin Interface        # Administrative functions
└── Health Monitoring      # System health and metrics

mongo_helper.py            # Database layer
├── Connection Management  # MongoDB connections
├── CRUD Operations        # Data operations
├── Schema Validation      # Data validation
└── Migration Tools        # Database migrations

redis_helper.py            # Cache layer
├── Cache Management       # Data caching
├── Session Storage        # Session handling
├── Rate Limiting          # Request throttling
└── Metrics Tracking       # Performance metrics
```

### Development Workflow

1. **Local Development**: Use `docker-compose.dev.yml`
2. **Testing**: Automated tests with pytest
3. **Staging**: Pre-production environment
4. **Production**: Docker Swarm or Kubernetes

### Code Standards

- **Python Style**: PEP 8 compliance
- **Documentation**: Comprehensive docstrings
- **Testing**: Unit and integration tests
- **Security**: Security-first development approach

## 🚀 Deployment Architecture

### Production Deployment

**Container Strategy**:
- Multi-stage Docker builds
- Optimized image layers
- Security scanning
- Resource optimization

**Orchestration Options**:
1. **Docker Compose**: Single-node deployment
2. **Docker Swarm**: Multi-node clustering
3. **Kubernetes**: Enterprise orchestration

### Scalability Considerations

**Horizontal Scaling**:
- Stateless application design
- External session storage (Redis)
- Database connection pooling
- Load balancer ready

**Vertical Scaling**:
- Resource-aware Docker limits
- Memory optimization
- CPU utilization monitoring
- Storage optimization

## 🔄 Maintenance & Operations

### Backup Strategy

**Database Backups**:
- Daily MongoDB dumps
- Point-in-time recovery
- Automated backup verification
- Offsite backup storage

**Configuration Backups**:
- Environment configuration
- Application state
- Docker configurations
- SSL certificates

### Update Procedures

**Application Updates**:
1. Test in staging environment
2. Database migration scripts
3. Zero-downtime deployment
4. Rollback procedures

**Security Updates**:
1. Regular dependency updates
2. Security patch management
3. Vulnerability scanning
4. Compliance monitoring

---

**For Deployment Instructions**: See [Docker-Setup.md](Docker-Setup.md)  
**For Project Overview**: See [README.md](README.md)
