@echo off
echo Starting JobHunter AI Backend...
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
)

REM Check .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure your API keys.
    echo   copy .env.example .env
    pause
    exit /b 1
)

REM Create upload directories
if not exist "uploads\resumes" mkdir uploads\resumes

echo Starting server on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
venv\Scripts\uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
