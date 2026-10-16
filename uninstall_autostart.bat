@echo off
title Hapus Auto-Start Bot Absensi E-Kinerja
color 0C
chcp 65001 >nul

echo ==============================================================
echo       MENGHAPUS AUTO-START BOT ABSENSI E-KINERJA
echo ==============================================================
echo.

set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_PATH=%STARTUP_DIR%\EkinerjaBotAbsen.lnk

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [SUKSES] Shortcut autostart berhasil dihapus dari Startup.
    echo Bot tidak akan berjalan otomatis lagi saat komputer menyala.
) else (
    echo [INFO] Shortcut autostart tidak ditemukan di folder Startup.
)

echo.
pause
