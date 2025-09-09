# PowerShell Development Deployment Script
# Windows version for local development with building

param(
    [string]$Action = "deploy"
)

$ErrorActionPreference = "Stop"

Write-Host "Level 7 Feeders - Development Deployment" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

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
        $installed = pip list --format=freeze
        $required = Get-Content requirements.txt
        $missing = @()
        
        foreach ($req in $required) {
            $package = $req.Split('==')[0]
            if ($installed -notmatch "^$package==") {
                $missing += $req
            }
        }
        
        if ($missing.Count -gt 0) {
            Write-Warning "Missing packages: $($missing -join ', ')"
            Write-Info "Installing missing packages..."
            pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to install packages"
                exit 1
            }
        }
        Write-Success "All Python dependencies satisfied"
    }
    catch {
        Write-Error "Failed to activate virtual environment or check dependencies: $_"
        exit 1
    }
    
    # Check Docker
    try {
        docker --version | Out-Null
        Write-Success "Docker is available"
    }
    catch {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }
    
    # Check Docker Compose
    try {
        docker compose version | Out-Null
        Write-Success "Docker Compose is available"
    }
    catch {
        Write-Error "Docker Compose is not available"
        exit 1
    }
    
    # Check environment file
    if (!(Test-Path ".env.production")) {
        Write-Error ".env.production file not found. Please copy from .env.production.template and configure."
        exit 1
    }
    Write-Success ".env.production found"
    
    # Check docker-compose.dev.yml
    if (!(Test-Path "docker-compose.dev.yml")) {
        Write-Error "docker-compose.dev.yml not found"
        exit 1
    }
    Write-Success "docker-compose.dev.yml found"
    
    # Check Dockerfile
    if (!(Test-Path "Dockerfile")) {
        Write-Error "Dockerfile not found"
        exit 1
    }
    Write-Success "Dockerfile found"
}

function Start-Deployment {
    Write-Info "Starting development deployment..."
    
    Test-Prerequisites
    
    Write-Info "Building images from local Dockerfile..."
    docker compose -f docker-compose.dev.yml --env-file .env.production build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    
    Write-Info "Stopping existing containers..."
    docker compose -f docker-compose.dev.yml --env-file .env.production down
    
    Write-Info "Starting development services..."
    docker compose -f docker-compose.dev.yml --env-file .env.production up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services"
        exit 1
    }
    
    Write-Success "Development deployment completed successfully!"
    
    # Show status
    Write-Info "Service status:"
    docker compose -f docker-compose.dev.yml --env-file .env.production ps
    
    Write-Info "Application should be available at:"
    Write-Host "  • http://localhost:5000" -ForegroundColor Yellow
    Write-Host "  • Development mode with hot reload enabled" -ForegroundColor Yellow
    
    Write-Info "To view logs, run: .\deploy-dev.ps1 logs"
    Write-Info "To stop services, run: .\deploy-dev.ps1 stop"
}

function Show-Logs {
    Write-Info "Showing development logs..."
    docker compose -f docker-compose.dev.yml --env-file .env.production logs -f
}

function Show-Status {
    Write-Info "Development service status:"
    docker compose -f docker-compose.dev.yml --env-file .env.production ps
}

function Stop-Services {
    Write-Info "Stopping development services..."
    docker compose -f docker-compose.dev.yml --env-file .env.production down
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development services stopped successfully"
    } else {
        Write-Error "Failed to stop services"
        exit 1
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "Level 7 Feeders - Development Deployment Script" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\deploy-dev.ps1 [action]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Green
    Write-Host "  deploy    - Build and deploy development environment (default)"
    Write-Host "  stop      - Stop all development services"
    Write-Host "  logs      - Show development service logs (follow mode)"
    Write-Host "  status    - Show development service status"
    Write-Host "  help      - Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\deploy-dev.ps1           # Deploy development environment"
    Write-Host "  .\deploy-dev.ps1 deploy    # Same as above"
    Write-Host "  .\deploy-dev.ps1 stop      # Stop all services"
    Write-Host "  .\deploy-dev.ps1 logs      # View logs"
    Write-Host "  .\deploy-dev.ps1 status    # Check status"
    Write-Host ""
    Write-Host "Note: This script builds images locally and enables development features"
    Write-Host "      like hot reload for faster development cycles."
    Write-Host ""
}

# Main execution
switch ($Action.ToLower()) {
    "deploy" { Start-Deployment }
    "stop" { Stop-Services }
    "logs" { Show-Logs }
    "status" { Show-Status }
    "help" { Show-Help }
    default {
        Write-Error "Unknown action: $Action"
        Show-Help
        exit 1
    }
}
