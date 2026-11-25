@echo off
echo Starting JobHunter AI Frontend...
echo.

REM Check node_modules
if not exist "node_modules\next" (
    echo Installing dependencies...
    npm install --legacy-peer-deps
)

REM Check .env.local
if not exist ".env.local" (
    echo Creating .env.local from example...
    copy .env.example .env.local
)

echo Starting Next.js on http://localhost:3000
echo.
npm run dev
