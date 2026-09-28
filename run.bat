@echo off
setlocal

:: Ensure working directory is always the script directory
cd /d "%~dp0"

title APEX Agent Launcher
color 0B

echo ===============================================================================
echo                APEX Agent: Self-Improving Multi-Agent Platform                
echo ===============================================================================
echo.

:: 1. Check Python Environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in .venv!
    echo Please create one with: python -m venv .venv
    echo And install dependencies: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

:: 2. Check Node.js Environment
where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js or npm is not installed or not in your PATH!
    echo Please install Node.js version 18 or higher from https://nodejs.org/
    pause
    exit /b 1
)

:: 3. Check .env File
if not exist ".env" (
    if exist ".env.example" (
        echo [*] .env not found. Copying from .env.example...
        copy /y ".env.example" ".env" >nul
        echo [*] Created .env file.
    )
)

:: 4. Run Database Migrations
echo [*] Checking and applying database migrations...
".venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Alembic check finished with a warning. Continuing...
)

echo.
echo ===============================================================================
echo Starting APEX Agent Services...
echo  - Backend:  http://127.0.0.1:8000
echo  - Frontend: http://localhost:3000
echo ===============================================================================
echo.

:: 5. Launch FastAPI Backend in a separate window
echo [*] Starting FastAPI Backend on port 8000...
start "APEX Backend (Port 8000)" cmd /k "cd /d ""%~dp0"" && title APEX Backend (Port 8000) && color 0A && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

:: Brief delay before launching frontend
ping 127.0.0.1 -n 3 >nul

:: 6. Launch Next.js Frontend in a separate window
echo [*] Starting Next.js Frontend on port 3000...
start "APEX Frontend (Port 3000)" cmd /k "cd /d ""%~dp0frontend"" && title APEX Frontend (Port 3000) && color 09 && npm run dev"

:: Brief delay before opening browser
ping 127.0.0.1 -n 4 >nul

:: 7. Open Browser
echo [*] Opening APEX Dashboard in default browser...
start http://localhost:3000

echo.
echo ===============================================================================
echo                     APEX Agent is now running!                                
echo ===============================================================================
echo   Dashboard:  http://localhost:3000
echo   API Docs:   http://127.0.0.1:8000/docs
echo   Health:     http://127.0.0.1:8000/health
echo.
echo Keep the backend and frontend terminal windows open while using the system.
echo To stop everything, close both windows or run 'stop.bat'.
echo ===============================================================================
echo.
pause
