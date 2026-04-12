# FastAPI Backend Startup Script - Fixed for Redis timeout issues
# Usage: .\START_BACKEND.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting Ravian Backend Server" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Navigate to the correct directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Check if venv exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Creating new venv..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$uvicornInstalled = & ".\venv\Scripts\python.exe" -m pip show uvicorn 2>$null
if (-not $uvicornInstalled) {
    Write-Host "Installing dependencies from app\requirements.txt..." -ForegroundColor Yellow
    & ".\venv\Scripts\python.exe" -m pip install -r app\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Test database connection first
Write-Host "Testing database connection..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -c "from app.core.database import test_connection; import sys; sys.exit(0 if test_connection() else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Database connection test failed!" -ForegroundColor Yellow
    Write-Host "Check your .env file DB settings:" -ForegroundColor Yellow
    Write-Host "  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME" -ForegroundColor Yellow
    Write-Host "Continuing anyway..." -ForegroundColor Yellow
}

# Start the server
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: If Redis is not running, the server will continue without it." -ForegroundColor Yellow
Write-Host "      Rate limiting will be disabled but the API will work." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Green

& ".\venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
