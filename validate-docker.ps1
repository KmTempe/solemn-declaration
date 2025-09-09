# PowerShell Docker and Dependencies Validation Script

Write-Host "Docker and Dependencies Validation" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "1. Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker is running" -ForegroundColor Green
    } else {
        throw "Docker not accessible"
    }
} catch {
    Write-Host "[ERROR] Docker is not running or accessible" -ForegroundColor Red
    exit 1
}

# Validate Dockerfile syntax
Write-Host ""
Write-Host "2. Validating Dockerfile..." -ForegroundColor Yellow
$buildResult = docker build -t l7-validation-test . 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dockerfile builds successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Dockerfile build failed" -ForegroundColor Red
    exit 1
}

# Check key dependencies in the built image
Write-Host ""
Write-Host "3. Checking dependencies in Docker image..." -ForegroundColor Yellow

$checkScript = @'
try:
    import flask
    print("[OK] Flask")
    import redis
    print("[OK] redis")
    import pymongo
    print("[OK] pymongo")
    import gunicorn
    print("[OK] gunicorn")
    import flask_session
    print("[OK] flask_session")
    import mobile_validate
    print("[OK] mobile_validate")
    print("All dependencies available!")
except Exception as e:
    print("[ERROR] Missing dependency: " + str(e))
'@

$depsCheck = docker run --rm l7-validation-test python -c $checkScript
Write-Host $depsCheck

# Test that the app exists
Write-Host ""
Write-Host "4. Testing app structure..." -ForegroundColor Yellow

if (Test-Path "app.py") {
    Write-Host "[OK] app.py exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] app.py missing" -ForegroundColor Red
}

# Validate production compose file
Write-Host ""
Write-Host "5. Validating production docker-compose..." -ForegroundColor Yellow
$composeResult = docker compose -f docker-compose.prod.yml config 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Production compose file is valid" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Production compose file has errors" -ForegroundColor Red
}

# Check that data directories exist
Write-Host ""
Write-Host "6. Checking production data directories..." -ForegroundColor Yellow

if (Test-Path ".env.production") {
    $dataRoot = (Get-Content ".env.production" | Where-Object { $_ -match "^DATA_ROOT_PATH=" }) -replace "DATA_ROOT_PATH=", ""
    $dataRoot = $dataRoot.Trim('"')
    
    if (Test-Path $dataRoot) {
        Write-Host "[OK] Data directory exists: $dataRoot" -ForegroundColor Green
        
        # Check subdirectories
        $subdirs = @("RedisData", "MongoDB", "logs", "nginx", "ssl")
        foreach ($subdir in $subdirs) {
            $path = Join-Path $dataRoot $subdir
            if (Test-Path $path) {
                Write-Host "  [OK] $subdir/" -ForegroundColor Green
            } else {
                Write-Host "  [MISSING] $subdir/" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "[WARNING] Data directory not found: $dataRoot" -ForegroundColor Yellow
        Write-Host "   Run: .\setup-production-dirs.ps1" -ForegroundColor White
    }
} else {
    Write-Host "[WARNING] .env.production not found" -ForegroundColor Yellow
    Write-Host "   Copy from .env.production.template" -ForegroundColor White
}

# Clean up test image
docker rmi l7-validation-test 2>$null | Out-Null

Write-Host ""
Write-Host "Validation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - Run: .\deploy-prod.sh deploy" -ForegroundColor White
Write-Host "  - Monitor: http://localhost/health" -ForegroundColor White
