#!/bin/bash

# TikTok View Bot Startup Script
clear

echo "========================================"
echo "   TIKTOK VIEW BOT PRO - STARTING"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 is not installed!"
    echo "Please install Python 3.8+: sudo apt install python3 python3-pip"
    exit 1
fi

# Check requirements
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] requirements.txt not found!"
    exit 1
fi

echo "[INFO] Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo "[INFO] Creating directories..."
mkdir -p logs
mkdir -p temp/screenshots
mkdir -p temp/cookies
mkdir -p database
mkdir -p proxies

echo "[INFO] Setting permissions..."
chmod +x main.py

echo "[INFO] Starting TikTok View Bot..."
echo ""

# Run bot
python3 main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[INFO] Bot stopped successfully"
else
    echo ""
    echo "[ERROR] Bot crashed! Check logs/bot.log"
fi