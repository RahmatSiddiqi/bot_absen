@echo off
title Pasang Bot Absen Otomatis Saat Komputer Dinyalakan (Auto-Start)
color 0B
chcp 65001 >nul

echo ==============================================================
echo       MEMASANG AUTO-START BOT ABSENSI E-KINERJA
echo ==============================================================
echo.

set SCRIPT_DIR=%~dp0
set VBS_TARGET=%SCRIPT_DIR%run_hidden.vbs
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT_PATH=%STARTUP_DIR%\EkinerjaBotAbsen.lnk

echo Membuat shortcut autostart di folder Startup Windows:
echo %SHORTCUT_PATH%
echo.

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_TARGET%\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'Bot Absensi E-Kinerja Otomatis 24/7'; $s.Save()"

if %errorlevel% equ 0 (
    echo ==============================================================
    echo [SUKSES] Auto-start berhasil dipasang!
    echo Bot akan otomatis berjalan di latar belakang setiap kali
    echo komputer dinyalakan / login ke Windows.
    echo ==============================================================
) else (
    echo [GAGAL] Terjadi kesalahan saat memasang shortcut autostart.
)

echo.
pause
