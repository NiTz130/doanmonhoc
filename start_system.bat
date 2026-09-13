@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Khong tim thay moi truong Python .venv.
    echo Hay chay: uv sync
    pause
    exit /b 1
)

start "Doan mon hoc - Backend" cmd /k ""%~dp0.venv\Scripts\python.exe" -m uvicorn api.app:app --reload"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000/"

endlocal
