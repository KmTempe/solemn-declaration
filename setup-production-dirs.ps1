# PowerShell script to set up production data directories
# Run this script before deploying to production

param(
    [string]$DataRootPath = "I:\forma\solemn-declaration\production-data"
)

Write-Host "Setting up production data directories..." -ForegroundColor Green
Write-Host "Data root path: $DataRootPath" -ForegroundColor Yellow

# Create main data directory
if (!(Test-Path $DataRootPath)) {
    New-Item -ItemType Directory -Path $DataRootPath -Force
    Write-Host "Created: $DataRootPath" -ForegroundColor Cyan
}

# Create subdirectories
$directories = @(
    "$DataRootPath\RedisData",
    "$DataRootPath\MongoDB", 
    "$DataRootPath\logs",
    "$DataRootPath\nginx",
    "$DataRootPath\ssl"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
        Write-Host "Created: $dir" -ForegroundColor Cyan
    } else {
        Write-Host "Exists: $dir" -ForegroundColor Gray
    }
}

# Set appropriate permissions (Windows)
Write-Host "Setting directory permissions..." -ForegroundColor Green
try {
    # Give full control to the current user and system
    icacls $DataRootPath /grant "${env:USERNAME}:(OI)(CI)F" /T > $null
    icacls $DataRootPath /grant "SYSTEM:(OI)(CI)F" /T > $null
    Write-Host "Permissions set successfully" -ForegroundColor Green
} catch {
    Write-Warning "Could not set permissions automatically. You may need to set them manually."
}

Write-Host ""
Write-Host "Production directories setup complete!" -ForegroundColor Green
Write-Host "You can now update your .env.production file with:" -ForegroundColor Yellow
Write-Host "DATA_ROOT_PATH=$DataRootPath" -ForegroundColor White
Write-Host ""
Write-Host "Directory structure created:" -ForegroundColor Yellow
Get-ChildItem -Path $DataRootPath -Directory | ForEach-Object {
    Write-Host "  [DIR] $($_.Name)" -ForegroundColor Cyan
}
