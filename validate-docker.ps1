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
Write-Host "   Building Docker image (this may take a few minutes)..." -ForegroundColor Gray

# Run docker build with live output
docker build -t l7-validation-test .
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Dockerfile builds successfully" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ERROR] Dockerfile build failed" -ForegroundColor Red
    Write-Host "   Check the build output above for details" -ForegroundColor Yellow
    exit 1
}

# Check key dependencies in the built image
Write-Host ""
Write-Host "3. Checking dependencies in Docker image..." -ForegroundColor Yellow

$pythonScript = 'import sys; deps = ["flask", "redis", "pymongo", "gunicorn", "flask_session", "mobile_validate", "bcrypt", "dotenv"]; names = ["Flask", "redis", "pymongo", "gunicorn", "flask_session", "mobile_validate", "bcrypt", "python-dotenv"]; failed = []; [failed.append(names[i]) if __import__(deps[i]) is None else print("[OK] " + names[i]) for i in range(len(deps)) if not (lambda: exec("import " + deps[i]) or True)()]; print("[SUCCESS] All dependencies available!") if not failed else (print("[FAILED] Missing: " + ", ".join(failed)) or sys.exit(1))'

# Simpler approach - test each dependency individually
$dependencies = @(
    @{module="flask"; name="Flask"},
    @{module="redis"; name="redis"},
    @{module="pymongo"; name="pymongo"},
    @{module="gunicorn"; name="gunicorn"},
    @{module="flask_session"; name="flask_session"},
    @{module="mobile_validate"; name="mobile_validate"},
    @{module="bcrypt"; name="bcrypt"},
    @{module="dotenv"; name="python-dotenv"}
)

$allDepsOk = $true
foreach ($dep in $dependencies) {
    $testResult = docker run --rm l7-validation-test python -c "import $($dep.module); print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] $($dep.name)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $($dep.name) - MISSING" -ForegroundColor Red
        $allDepsOk = $false
    }
}

if ($allDepsOk) {
    Write-Host "[SUCCESS] All critical dependencies available!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Some dependencies are missing" -ForegroundColor Red
    exit 1
}

# Test that the app exists
Write-Host ""
Write-Host "4. Testing app structure..." -ForegroundColor Yellow

$requiredFiles = @("app.py", "mongo_helper.py", "redis_helper.py", "redis_session_simple.py", "requirements.txt")
$allFilesExist = $true

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file exists" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] $file missing" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "[ERROR] Critical files missing" -ForegroundColor Red
    exit 1
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

# Check documentation structure
Write-Host ""
Write-Host "7. Checking documentation..." -ForegroundColor Yellow

$docFiles = @("README.md", "Docker-Setup.md")
foreach ($doc in $docFiles) {
    if (Test-Path $doc) {
        Write-Host "  [OK] $doc exists" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $doc" -ForegroundColor Red
    }
}

# Clean up test image
docker rmi l7-validation-test 2>$null | Out-Null

Write-Host ""
Write-Host "Validation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - Deploy: .\deploy-prod.ps1 deploy" -ForegroundColor White
Write-Host "  - Monitor: http://localhost:5000/health" -ForegroundColor White
Write-Host "  - Admin: http://localhost:5000/admin" -ForegroundColor White
Write-Host "  - Documentation: See README.md and Docker-Setup.md" -ForegroundColor White
