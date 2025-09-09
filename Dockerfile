# Use Alpine as base for smaller image size - Updated to latest LTS version
FROM python:3.12-alpine3.20

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    wget \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove build dependencies to reduce image size
    apk del gcc musl-dev python3-dev libffi-dev openssl-dev

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PATH="/usr/local/bin:${PATH}"

# Create and switch to non-root user
RUN adduser -D -s /bin/sh appuser && \
    mkdir -p /app/submissions /app/logs && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create necessary directories for the app
RUN mkdir -p submissions logs

# Expose port
EXPOSE 5000

# Health check using wget (lighter than requests import)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "--access-logfile", "/app/logs/access.log", "--error-logfile", "/app/logs/error.log", "app:app"]
