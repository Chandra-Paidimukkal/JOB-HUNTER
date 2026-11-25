@echo off
title Stopping JobHunter AI...
echo.
echo  Stopping JobHunter AI services...
echo.

REM Kill uvicorn (backend)
taskkill /F /FI "WINDOWTITLE eq JobHunter AI*" /T >nul 2>&1

REM Kill processes by port
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo  Services stopped.
echo.
timeout /t 2 /nobreak >nul
