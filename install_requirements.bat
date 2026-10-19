@echo off
title Install Modul Python Bot Absen
color 0A
chcp 65001 >nul
cd /d "%~dp0"

echo ==============================================================
echo       MENGINSTALL MODUL / LIBRARY PYTHON YANG DIBUTUHKAN
echo ==============================================================
echo.
pip install -r requirements.txt

echo.
echo ==============================================================
echo Selesai! Sekarang semua modul sudah terpasang.
echo ==============================================================
pause
