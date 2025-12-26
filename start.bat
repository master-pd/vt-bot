@echo off
chcp 65001 > nul
title TikTok View Bot Pro v2.5
color 0A

echo ========================================
echo     TIKTOK VIEW BOT PRO - STARTING
echo ========================================
echo.

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check requirements
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo [INFO] Checking dependencies...
pip install -r requirements.txt --quiet

echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "temp" mkdir temp
if not exist "temp\screenshots" mkdir temp\screenshots
if not exist "temp\cookies" mkdir temp\cookies
if not exist "database" mkdir database

echo [INFO] Starting TikTok View Bot...
echo.

REM Run the bot
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Bot crashed! Check logs/bot.log for details
) else (
    echo.
    echo [INFO] Bot stopped successfully
)

pause