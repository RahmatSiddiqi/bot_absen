@echo off
title Bot Absensi E-Kinerja Otomatis 24/7
color 0A
chcp 65001 >nul
cd /d "%~dp0"

set "PY=python"
if exist "C:\laragon\bin\python\python-3.10\python.exe" (
    set "PY=C:\laragon\bin\python\python-3.10\python.exe"
)

echo ==============================================================
echo       🤖 MEMULAI BOT ABSENSI E-KINERJA (24/7)
echo ==============================================================
echo Menggunakan Python: %PY%
echo.

"%PY%" main.py

if %errorlevel% neq 0 (
    echo.
    echo [INFO] Bot berhenti atau terjadi error.
    pause
)
