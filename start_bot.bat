@echo off
title Bot Absensi E-Kinerja Otomatis 24/7
color 0A
chcp 65001 >nul

echo ==============================================================
echo       🤖 MEMULAI BOT ABSENSI E-KINERJA (24/7)
echo ==============================================================
echo.

cd /d "%~dp0"

:: Cek Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di sistem Anda!
    echo Silakan install Python terlebih dahulu dari https://www.python.org/
    pause
    exit /b 1
)

:: Cek & Install Requirements jika belum terpasang
pip install -r requirements.txt --quiet >nul 2>&1

:: Jalankan Bot
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Bot berhenti atau terjadi error.
    pause
)
