@echo off
title Enkripsi Password E-Kinerja (Windows DPAPI)
color 0B
chcp 65001 >nul
cd /d "%~dp0"

set "PY=python"
if exist "C:\laragon\bin\python\python-3.10\python.exe" (
    set "PY=C:\laragon\bin\python\python-3.10\python.exe"
)

"%PY%" setup_secure_credentials.py

echo.
pause
