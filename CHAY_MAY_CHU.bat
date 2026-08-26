@echo off
title HUY HOANG - MAY CHU AI VIETNAMESE TTS
color 0b
chcp 65001 >nul
cls

echo =========================================================================
echo       HUY HOANG STUDIO - MAY CHU AI SINH GIONG NOI VIETNAMESE (TTS)
echo                       Hotline: 0933116860
echo =========================================================================
echo.
echo [1/3] Kiem tra moi truong Python...
python --version
if %errorlevel% neq 0 (
    color 0c
    echo [LOI] May tinh chua cai dat Python hoac chua them vao PATH!
    pause
    exit /b
)

echo.
echo [2/3] Dia chi ket noi noi bo (WiFi / Mang LAN):
echo       - Tren may tinh nay : http://127.0.0.1:8000
echo       - Tren dien thoai   : http://192.168.1.8:8000
echo.
echo [3/3] Dang khoi dong May Chu AI...
echo =========================================================================
echo   LUU Y: Khong dong cua so nay trong khi su dung tren Dien Thoai!
echo =========================================================================
echo.

python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

pause
