# APEX Agent PowerShell Launcher
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "               APEX Agent: Self-Improving Multi-Agent Platform                " -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Python virtual environment not found at $PythonExe" -ForegroundColor Red
    Write-Host "Please create one with: python -m venv .venv"
    Write-Host "And install dependencies: .venv\Scripts\pip install -r requirements.txt"
    Read-Host "Press Enter to exit..."
    exit 1
}

# 2. Check Node
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Node.js or npm is not in your PATH." -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/"
    Read-Host "Press Enter to exit..."
    exit 1
}

# 3. Check .env
$EnvFile = Join-Path $ScriptDir ".env"
$EnvExample = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $EnvFile)) {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "[*] Created .env from .env.example." -ForegroundColor Yellow
    }
}

# 4. Migrations
Write-Host "[*] Checking and applying database migrations..." -ForegroundColor Green
& $PythonExe -m alembic upgrade head

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "Starting APEX Agent Services..." -ForegroundColor Cyan
Write-Host " - Backend:  http://127.0.0.1:8000" -ForegroundColor White
Write-Host " - Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# 5. Launch Backend
Write-Host "[*] Launching FastAPI Backend on port 8000..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/k", "cd /d `"$ScriptDir`" && title APEX Backend (Port 8000) && color 0A && `"$PythonExe`" -m uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 3

# 6. Launch Frontend
$FrontendDir = Join-Path $ScriptDir "frontend"
Write-Host "[*] Launching Next.js Frontend on port 3000..." -ForegroundColor Green
Start-Process cmd -ArgumentList "/k", "cd /d `"$FrontendDir`" && title APEX Frontend (Port 3000) && color 09 && npm run dev"

Start-Sleep -Seconds 4

# 7. Open Browser
Write-Host "[*] Opening APEX Dashboard in your default browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "                    APEX Agent is now running!                                " -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:3000"
Write-Host "  API Docs:   http://127.0.0.1:8000/docs"
Write-Host "  Health:     http://127.0.0.1:8000/health"
Write-Host ""
Write-Host "Keep the two opened terminal windows open while using the system."
Write-Host "To stop everything, simply run .\stop.bat or close both windows."
Write-Host "===============================================================================" -ForegroundColor Green
Write-Host ""
