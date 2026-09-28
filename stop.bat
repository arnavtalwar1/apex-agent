@echo off
cd /d "%~dp0"
title Stop APEX Agent
color 0C

echo ===============================================================================
echo                      Stopping APEX Agent Services...                          
echo ===============================================================================
echo.

echo [*] Terminating Python/Uvicorn processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a 2>nul
)

echo [*] Terminating Node.js/Next.js processes on port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /F /PID %%a 2>nul
)

echo.
echo [*] APEX Agent services have been stopped.
echo ===============================================================================
echo.
pause
