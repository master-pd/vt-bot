#!/bin/bash
echo "Installing VT View Tester Pro..."
echo "================================"

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "Installing Python..."
    pkg install python -y
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright
echo "Installing Playwright browsers..."
playwright install chromium

# Create necessary directories
echo "Creating directories..."
mkdir -p data/{accounts,proxies,logs,backups}

# Initialize database
echo "Initializing database..."
python3 -c "from database.models import init_database; init_database()"

# Make scripts executable
chmod +x run.py

echo "Installation completed!"
echo "Run: python run.py --mode terminal"