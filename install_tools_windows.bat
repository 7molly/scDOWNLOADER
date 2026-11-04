@echo off
chcp 65001 >nul
title Установка yt-dlp и ffmpeg для Windows

echo ========================================================
echo   Установка yt-dlp и ffmpeg через Windows Package Manager (winget)
echo ========================================================
echo.

where winget >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ВНИМАНИЕ] Утилита winget не найдена.
    echo Пожалуйста, установите yt-dlp и ffmpeg вручную:
    echo 1. yt-dlp: https://github.com/yt-dlp/yt-dlp/releases (скачайте yt-dlp.exe и положите в эту папку)
    echo 2. ffmpeg: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)
    echo.
    pause
    exit /b 1
)

echo [1/2] Установка yt-dlp...
winget install --id yt-dlp.yt-dlp -e --accept-source-agreements --accept-package-agreements

echo.
echo [2/2] Установка ffmpeg...
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements

echo.
echo ========================================================
echo   Установка завершена! Теперь запустите run_windows.bat
echo ========================================================
pause
