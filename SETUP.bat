@echo off
title JobHunter AI — First Time Setup
color 0E
cls

echo.
echo  ================================================================
echo   J O B H U N T E R   A I   —   S E T U P
echo  ================================================================
echo.
echo  This will install all dependencies (takes 2-5 minutes).
echo  Internet connection required.
echo.
pause

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

REM ── Check Python ────────────────────────────────────────────────
echo.
echo [Step 1/4] Checking Python...
python --version 2>nul
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Install Python 3.11+ from https://www.python.org/downloads/
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)
echo  Python OK

REM ── Check Node.js ───────────────────────────────────────────────
echo [Step 2/4] Checking Node.js...
node --version 2>nul
if errorlevel 1 (
    echo  ERROR: Node.js not found.
    echo  Install from https://nodejs.org/
    start "" "https://nodejs.org/"
    pause
    exit /b 1
)
echo  Node.js OK

REM ── Backend setup ───────────────────────────────────────────────
echo.
echo [Step 3/4] Setting up backend Python environment...
cd /d "%BACKEND%"

if not exist "venv\Scripts\python.exe" (
    echo  Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: Failed to create venv
        pause
        exit /b 1
    )
)

echo  Installing Python packages (this may take 2-3 minutes)...
venv\Scripts\pip install -r requirements.txt --quiet --no-warn-script-location
if errorlevel 1 (
    echo  ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  Backend packages installed

REM ── Frontend setup ──────────────────────────────────────────────
echo.
echo [Step 4/4] Setting up frontend Node packages...
cd /d "%FRONTEND%"

if not exist "node_modules\next" (
    echo  Installing npm packages (this may take 1-2 minutes)...
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        echo  ERROR: npm install failed
        pause
        exit /b 1
    )
)
echo  Frontend packages installed

REM ── Setup complete ──────────────────────────────────────────────
echo.
echo  ================================================================
echo   SETUP COMPLETE!
echo  ================================================================
echo.
echo  Your .env is already configured with:
echo    Groq API Key: SET
echo    Model: openai/gpt-oss-120b
echo.
echo  IMPORTANT: Before starting, set your DATABASE_URL in:
echo    %BACKEND%\.env
echo.
echo  Quick options:
echo    Free cloud DB:  https://supabase.com (copy connection string)
echo    Local DB:       Install PostgreSQL, create 'jobhunter_ai' database
echo.
echo  Once database is configured, run:
echo    START_JOBHUNTER.bat
echo.
echo  ================================================================
pause
