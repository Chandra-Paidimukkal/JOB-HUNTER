@echo off
title JobHunter AI — Launcher
color 0A
cls

echo.
echo  ================================================================
echo   J O B H U N T E R   A I
echo   Your Personal AI Job Hunting Agent
echo  ================================================================
echo   Groq AI  ^|  Next.js  ^|  FastAPI  ^|  SQLite/PostgreSQL
echo  ================================================================
echo.

REM ── Resolve root directory ──────────────────────────────────────
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "PYTHON=%BACKEND%\venv\Scripts\python.exe"
set "UVICORN=%BACKEND%\venv\Scripts\uvicorn.exe"
set "NPM=node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js""

echo  Root : %ROOT%
echo  Back : %BACKEND%
echo  Front: %FRONTEND%
echo.

REM ── STEP 1: Check Python venv ───────────────────────────────────
echo [1/5] Checking Python virtual environment...
if not exist "%PYTHON%" (
    echo.
    echo  Python venv not found. Running setup...
    echo.
    cd /d "%BACKEND%"
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: python -m venv failed.
        echo  Install Python 3.11+ from https://www.python.org/downloads/
        pause & exit /b 1
    )
    venv\Scripts\pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo  ERROR: pip install failed. Check internet connection.
        pause & exit /b 1
    )
    echo  Setup complete!
)
echo       Python venv: OK

REM ── STEP 2: Check .env ──────────────────────────────────────────
echo [2/5] Checking configuration...
if not exist "%BACKEND%\.env" (
    echo  .env not found — copying from .env.example
    copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
)
echo       .env: OK

REM ── STEP 3: Check npm packages ──────────────────────────────────
echo [3/5] Checking Node packages...
if not exist "%FRONTEND%\node_modules\next" (
    echo  Installing npm packages (first run — takes 2 min)...
    cd /d "%FRONTEND%"
    call node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install --legacy-peer-deps --silent
    if errorlevel 1 (
        echo  ERROR: npm install failed
        pause & exit /b 1
    )
)
echo       Node modules: OK

REM ── STEP 4: Create uploads folder ──────────────────────────────
echo [4/5] Preparing directories...
if not exist "%BACKEND%\uploads\resumes" mkdir "%BACKEND%\uploads\resumes" 2>nul
if not exist "%FRONTEND%\.env.local" (
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > "%FRONTEND%\.env.local"
)
echo       Directories: OK

REM ── STEP 5: Verify Groq key & DB ───────────────────────────────
echo [5/5] Verifying Groq API and database...
cd /d "%BACKEND%"
"%PYTHON%" -c "
import sys, os
sys.path.insert(0, '.')
os.chdir('.')
from app.core.config import settings
from app.core.database import Base, engine
import app.models
Base.metadata.create_all(bind=engine)
print('DB:OK')
key = settings.GROQ_API_KEY
if key and key != 'your_groq_api_key_here':
    print('KEY:SET')
else:
    print('KEY:MISSING')
" 2>nul > "%TEMP%\jh_check.txt"
findstr "DB:OK" "%TEMP%\jh_check.txt" >nul && echo       Database: OK
findstr "KEY:SET" "%TEMP%\jh_check.txt" >nul && echo       Groq Key: SET ^(openai/gpt-oss-120b^)
findstr "KEY:MISSING" "%TEMP%\jh_check.txt" >nul && (
    echo.
    echo  WARNING: GROQ_API_KEY is not set in backend\.env
    echo  Edit backend\.env and set your key from console.groq.com
    echo.
)
del "%TEMP%\jh_check.txt" 2>nul

echo.
echo  ================================================================
echo   Starting services...
echo  ================================================================
echo.

REM ── Stop any existing processes on these ports ──────────────────
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":3000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

REM ── Launch Backend ──────────────────────────────────────────────
echo  Launching Backend on http://localhost:8000 ...
start "JobHunter-Backend" /D "%BACKEND%" /MIN cmd /k "^
color 0B ^& ^
title JobHunter AI Backend - http://localhost:8000 ^& ^
echo. ^& ^
echo  ========================================= ^& ^
echo   BACKEND  ^|  http://localhost:8000 ^& ^
echo   API DOCS ^|  http://localhost:8000/docs ^& ^
echo  ========================================= ^& ^
echo. ^& ^
venv\Scripts\uvicorn app.main:app --reload --reload-dir app --port 8000 --host 127.0.0.1 ^& ^
echo. ^& echo  Backend stopped. ^& pause"

echo  Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM ── Verify backend ──────────────────────────────────────────────
curl -s -f http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo  Backend still starting — waiting 5 more seconds...
    timeout /t 5 /nobreak >nul
)
curl -s -f http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo  WARNING: Backend may not be fully started yet.
    echo  Check the Backend window for errors.
    echo.
) else (
    echo       Backend: RUNNING
)

REM ── Launch Frontend ─────────────────────────────────────────────
echo.
echo  Launching Frontend on http://localhost:3000 ...
start "JobHunter-Frontend" /D "%FRONTEND%" /MIN cmd /k "^
color 0D ^& ^
title JobHunter AI Frontend - http://localhost:3000 ^& ^
echo. ^& ^
echo  ========================================= ^& ^
echo   FRONTEND  ^|  http://localhost:3000 ^& ^
echo  ========================================= ^& ^
echo. ^& ^
node "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" run dev ^& ^
echo. ^& echo  Frontend stopped. ^& pause"

echo  Waiting for frontend to compile (20 seconds)...
timeout /t 20 /nobreak >nul

REM ── Open browser ────────────────────────────────────────────────
echo  Opening browser...
start "" "http://localhost:3000"

REM ── Done ────────────────────────────────────────────────────────
echo.
echo  ================================================================
echo.
echo   JobHunter AI is RUNNING!
echo.
echo   App      -^>  http://localhost:3000
echo   API      -^>  http://localhost:8000
echo   API Docs -^>  http://localhost:8000/docs
echo.
echo   First time? Click "Create one free" to register.
echo   Then complete the 4-step profile setup.
echo   Upload your resume — Groq AI will analyze it.
echo   Run job discovery — real jobs from Remotive API.
echo   AI match jobs to your profile (0-100 score).
echo   Generate outreach emails in the AI Outreach Studio.
echo.
echo   AI Model : openai/gpt-oss-120b  (via Groq)
echo   Database : SQLite (./backend/jobhunter.db)
echo.
echo   To stop: Run STOP_JOBHUNTER.bat
echo            or close the two background terminal windows
echo.
echo  ================================================================
echo.
pause
