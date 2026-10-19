@echo off
title Uji Status Login E-Kinerja
color 0B
chcp 65001 >nul
cd /d "%~dp0"

set "PY=python"
if exist "C:\laragon\bin\python\python-3.10\python.exe" (
    set "PY=C:\laragon\bin\python\python-3.10\python.exe"
)

echo ==============================================================
echo       MEMERIKSA STATUS LOGIN DAN ABSENSI E-KINERJA
echo ==============================================================
echo.
echo Menggunakan Python: %PY%
echo Menghubungi server E-Kinerja...
echo.

"%PY%" main.py --test-login

echo.
echo ==============================================================
pause
