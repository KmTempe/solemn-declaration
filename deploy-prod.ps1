# PowerShell Production Deployment Script
# Windows version of deploy-prod.sh

param(
    [string]$Action = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "Level 7 Feeders - Production Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

function Write-Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Blue
}

function Write-Success($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}

function Write-Warning($msg) {
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
}

function Write-Error($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
}

function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if virtual environment exists
    if (!(Test-Path "venv\Scripts\Activate.ps1")) {
        Write-Warning "Virtual environment not found. Creating one..."
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            exit 1
        }
        Write-Success "Virtual environment created"
    } else {
        Write-Success "Virtual environment found"
    }
    
    # Activate virtual environment and check dependencies
    Write-Info "Checking Python dependencies..."
    try {
        & .\venv\Scripts\Activate.ps1
        $pythonVersion = python --version
        Write-Success "Using $pythonVersion in virtual environment"
        
        # Check if requirements are installed
        $pipList = pip freeze
        if ($pipList -match "Flask==") {
            Write-Success "Dependencies already installed"
        } else {
            Write-Info "Installing dependencies..."
            pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install dependencies"
                exit 1
            }
            Write-Success "Dependencies installed"
        }
    } catch {
        Write-Error "Failed to setup Python environment"
        exit 1
    }
    
    # Check Docker - use a simpler test command
    Write-Info "Testing Docker connection..."
    try {
        $ErrorActionPreference = "SilentlyContinue"
        $dockerResult = docker version --format "{{.Client.Version}}" 2>$null
        $ErrorActionPreference = "Stop"
        
        if ($LASTEXITCODE -eq 0 -and $dockerResult) {
            Write-Success "Docker is running (version detected)"
        } else {
            Write-Error "Docker is not accessible"
            exit 1
        }
    } catch {
        Write-Error "Docker test failed"
        exit 1
    }
    
    # Check docker-compose
    Write-Info "Testing docker-compose..."
    try {
        $ErrorActionPreference = "SilentlyContinue"
        $null = docker compose version --short 2>$null
        $ErrorActionPreference = "Stop"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "docker-compose available"
        } else {
            Write-Error "docker-compose not available"
            exit 1
        }
    } catch {
        Write-Error "docker-compose test failed"
        exit 1
    }
    
    # Check .env.production
    if (!(Test-Path ".env.production")) {
        Write-Error ".env.production not found"
        exit 1
    }
    Write-Success ".env.production found"
    
    # Check docker-compose.prod.yml
    if (!(Test-Path "docker-compose.prod.yml")) {
        Write-Error "docker-compose.prod.yml not found"
        exit 1
    }
    Write-Success "docker-compose.prod.yml found"
}

function Start-Deployment {
    Write-Info "Starting deployment..."
    
    Test-Prerequisites
    
    Write-Info "Pulling latest images from Docker Hub..."
    docker compose -f docker-compose.prod.yml --env-file .env.production pull
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to pull images"
        exit 1
    }
    
    Write-Info "Stopping existing containers..."
    docker compose -f docker-compose.prod.yml --env-file .env.production down
    
    Write-Info "Starting services..."
    docker compose -f docker-compose.prod.yml --env-file .env.production up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services"
        exit 1
    }
    
    Write-Info "Waiting for health check..."
    $attempts = 0
    $maxAttempts = 30
    
    do {
        Start-Sleep -Seconds 10
        $attempts++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "Application is healthy!"
                break
            }
        } catch {
            Write-Info "Waiting... ($attempts/$maxAttempts)"
        }
    } while ($attempts -lt $maxAttempts)
    
    if ($attempts -eq $maxAttempts) {
        Write-Error "Health check failed"
        exit 1
    }
    
    Write-Host ""
    Write-Success "[SUCCESS] Deployment completed successfully!"
    Write-Host ""
    Write-Host "Application URLs:" -ForegroundColor Cyan
    Write-Host "  - Form: http://localhost:5000/" -ForegroundColor White
    Write-Host "  - Health: http://localhost:5000/health" -ForegroundColor White
    Write-Host ""
}

function Stop-Deployment {
    Write-Warning "Stopping deployment..."
    docker compose -f docker-compose.prod.yml --env-file .env.production down
    Write-Success "Containers stopped"
}

function Show-Health {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing
        $health = $response.Content | ConvertFrom-Json
        Write-Host ($health | ConvertTo-Json -Depth 5) -ForegroundColor Green
    } catch {
        Write-Error "Health check failed: $_"
    }
}

function Show-Logs {
    Write-Info "Showing logs (Ctrl+C to exit)..."
    docker compose -f docker-compose.prod.yml --env-file .env.production logs -f
}

function Show-Status {
    Write-Info "Container Status:"
    docker compose -f docker-compose.prod.yml --env-file .env.production ps
}

function Show-Help {
    Write-Host ""
    Write-Host "Level 7 Feeders - Production Deployment Script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy-prod.ps1 [action]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  deploy   - Deploy to production (default)" -ForegroundColor White
    Write-Host "  stop     - Stop all containers" -ForegroundColor White
    Write-Host "  health   - Show health status" -ForegroundColor White
    Write-Host "  logs     - Show application logs" -ForegroundColor White
    Write-Host "  status   - Show container status" -ForegroundColor White
    Write-Host "  help     - Show this help" -ForegroundColor White
    Write-Host ""
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" { Start-Deployment }
    "stop" { Stop-Deployment }
    "health" { Show-Health }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "help" { Show-Help }
    default {
        Write-Error "Unknown action: $Action"
        Show-Help
        exit 1
    }
}
