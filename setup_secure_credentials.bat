@echo off
title Enkripsi Password E-Kinerja (Windows DPAPI)
color 0B
chcp 65001 >nul
cd /d "%~dp0"

python setup_secure_credentials.py

echo.
pause
