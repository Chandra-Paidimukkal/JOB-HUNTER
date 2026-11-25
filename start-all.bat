@echo off
echo ======================================
echo   JobHunter AI — Starting All Services
echo ======================================
echo.
echo Starting Backend (port 8000)...
start "JobHunter Backend" cmd /k "cd /d backend && start.bat"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Frontend (port 3000)...
start "JobHunter Frontend" cmd /k "cd /d frontend && start.bat"

echo.
echo ======================================
echo   Services starting:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo ======================================
echo.
echo Remember to set your GROQ_API_KEY in backend\.env
