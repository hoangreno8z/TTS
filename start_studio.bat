@echo off
title LAPQUE Personal Vietnamese TTS Studio
cd /d "%~dp0"
echo ========================================================
echo   DANG KHOI DONG LAPQUE PERSONAL VIETNAMESE TTS STUDIO
echo ========================================================
echo.
python run_studio.py
if %errorlevel% neq 0 (
    echo.
    echo [THONG BAO] Dang khoi dong bang Uvicorn truc tiep...
    uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
)
pause
