#!/bin/bash
# Docker and Dependencies Validation Script

echo "🔍 Docker and Dependencies Validation"
echo "====================================="

# Check if Docker is running
echo "1. Checking Docker status..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running or accessible"
    exit 1
fi

# Validate Dockerfile syntax
echo ""
echo "2. Validating Dockerfile..."
if docker build -t l7-validation-test . >/dev/null 2>&1; then
    echo "✅ Dockerfile builds successfully"
else
    echo "❌ Dockerfile build failed"
    exit 1
fi

# Check key dependencies in the built image
echo ""
echo "3. Checking dependencies in Docker image..."
DEPS_CHECK=$(docker run --rm l7-validation-test python -c "
import sys
deps = {
    'Flask': 'Flask',
    'redis': 'redis', 
    'pymongo': 'pymongo',
    'gunicorn': 'gunicorn',
    'flask_session': 'Flask-Session',
    'mobile_validate': 'mobile_validate'
}

missing = []
for module, package in deps.items():
    try:
        __import__(module)
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - MISSING')
        missing.append(package)

if missing:
    print(f'Missing packages: {missing}')
    sys.exit(1)
else:
    print('All dependencies available!')
")

echo "$DEPS_CHECK"

# Test that the app can be imported
echo ""
echo "4. Testing app import..."
APP_TEST=$(docker run --rm -v "$(pwd):/app" l7-validation-test python -c "
try:
    import app
    print('✅ App imports successfully')
except Exception as e:
    print(f'❌ App import failed: {e}')
    exit(1)
")

echo "$APP_TEST"

# Validate production compose file
echo ""
echo "5. Validating production docker-compose..."
if docker compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
    echo "✅ Production compose file is valid"
else
    echo "❌ Production compose file has errors"
    exit 1
fi

# Check that data directories exist
echo ""
echo "6. Checking production data directories..."
if [ -f ".env.production" ]; then
    DATA_ROOT=$(grep "^DATA_ROOT_PATH=" .env.production | cut -d'=' -f2 | tr -d '"')
    if [ -d "$DATA_ROOT" ]; then
        echo "✅ Data directory exists: $DATA_ROOT"
        
        # Check subdirectories
        for subdir in RedisData MongoDB logs nginx ssl; do
            if [ -d "$DATA_ROOT/$subdir" ]; then
                echo "  ✅ $subdir/"
            else
                echo "  ❌ $subdir/ - missing"
            fi
        done
    else
        echo "⚠️  Data directory not found: $DATA_ROOT"
        echo "   Run: ./setup-production-dirs.ps1"
    fi
else
    echo "⚠️  .env.production not found"
    echo "   Copy from .env.production.template"
fi

# Clean up test image
docker rmi l7-validation-test >/dev/null 2>&1

echo ""
echo "🎉 Validation complete!"
echo ""
echo "Next steps:"
echo "  - Run: ./deploy-prod.sh deploy"
echo "  - Monitor: http://localhost/health"
