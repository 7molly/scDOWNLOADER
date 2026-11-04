@echo off
chcp 65001 >nul
title SoundCloud & Video Downloader

echo ========================================================
echo   Запуск SoundCloud & Video Downloader для Windows...
echo ========================================================

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%~dp0app.py"
    exit /b 0
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py "%~dp0app.py"
    exit /b 0
)

echo.
echo [ОШИБКА] Python не найден на вашем компьютере!
echo Скачайте и установите Python с официального сайта:
echo https://www.python.org/downloads/
echo.
echo ВАЖНО: Во время установки обязательно поставьте галочку:
echo "Add python.exe to PATH"
echo.
pause
