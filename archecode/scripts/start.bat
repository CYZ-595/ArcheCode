@echo off
REM ArcheCode Startup Script for Windows
REM Starts both backend and frontend services

echo ============================================
echo   ArcheCode - AI Code Archaeology Platform
echo ============================================
echo.

REM Check for .env file
if not exist "%~dp0..\..env" (
    if exist "%~dp0..\..env.example" (
        echo [INFO] No .env file found. Copying from .env.example...
        copy "%~dp0..\..env.example" "%~dp0..\..env"
        echo [INFO] Please edit .env and add your OPENAI_API_KEY
    )
)

REM Start backend
echo [1/2] Starting backend...
cd /d "%~dp0..\backend"

if not exist "venv" (
    echo   Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo   Backend starting on http://localhost:8000
start "ArcheCode Backend" cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Start frontend
echo [2/2] Starting frontend...
cd /d "%~dp0..\frontend"

if not exist "node_modules" (
    echo   Installing npm dependencies...
    call npm install
)

echo   Frontend starting on http://localhost:3000
start "ArcheCode Frontend" cmd /c "npm run dev"

echo.
echo ============================================
echo   ArcheCode is running!
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to stop all services...
pause >nul

taskkill /FI "WINDOWTITLE eq ArcheCode Backend*" /F 2>nul
taskkill /FI "WINDOWTITLE eq ArcheCode Frontend*" /F 2>nul
echo Services stopped.
