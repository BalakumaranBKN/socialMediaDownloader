@echo off
echo ========================================================
echo   Starting Social Media Downloader (Backend + Frontend)
echo ========================================================

echo [1/2] Starting Python FastAPI Backend on port 8000...
start "OmniGrab Backend" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Angular Frontend on port 4200...
start "OmniGrab Frontend" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo Application will be available at: http://localhost:4200
echo Backend API docs available at:   http://localhost:8000/docs
echo ========================================================
pause
