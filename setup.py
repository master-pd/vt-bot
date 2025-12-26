#!/usr/bin/env python3
"""
VT View Tester - Setup Script
Installation and configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_colored(text, color_code):
    """Print colored text"""
    print(f"\033[{color_code}m{text}\033[0m")

def check_python_version():
    """Check Python version"""
    print_colored("🔍 Checking Python version...", "36")
    
    if sys.version_info < (3, 12):
        print_colored(f"❌ Python 3.12+ required, but found {sys.version}", "31")
        return False
    
    print_colored(f"✅ Python {sys.version} detected", "32")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_colored("📦 Installing dependencies...", "36")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print_colored("❌ requirements.txt not found", "31")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print_colored("✅ Dependencies installed successfully", "32")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install dependencies: {e}", "31")
        return False

def install_playwright():
    """Install Playwright browsers"""
    print_colored("🌐 Installing Playwright browsers...", "36")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "playwright", "install", "chromium"
        ])
        print_colored("✅ Playwright installed successfully", "32")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install Playwright: {e}", "31")
        return False

def create_directories():
    """Create necessary directories"""
    print_colored("📁 Creating directories...", "36")
    
    directories = [
        "data",
        "data/accounts",
        "data/proxies",
        "data/logs",
        "data/backups",
        "data/reports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_colored(f"  Created: {directory}", "32")
    
    print_colored("✅ Directories created", "32")
    return True

def initialize_database():
    """Initialize database"""
    print_colored("💾 Initializing database...", "36")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from database.models import init_database
        
        init_database()
        print_colored("✅ Database initialized", "32")
        return True
    except Exception as e:
        print_colored(f"❌ Failed to initialize database: {e}", "31")
        return False

def create_sample_files():
    """Create sample configuration files"""
    print_colored("📝 Creating sample files...", "36")
    
    # Sample accounts file
    accounts_file = Path("data/accounts/accounts.json")
    if not accounts_file.exists():
        sample_accounts = [
            {
                "username": "dummy_account1",
                "password": "password123",
                "status": "active",
                "notes": "Sample account 1"
            },
            {
                "username": "dummy_account2",
                "password": "password456",
                "status": "active",
                "notes": "Sample account 2"
            }
        ]
        
        import json
        with open(accounts_file, 'w') as f:
            json.dump(sample_accounts, f, indent=2)
        
        print_colored("  Created sample accounts file", "32")
    
    # Sample proxies file
    proxies_file = Path("data/proxies/proxies.txt")
    if not proxies_file.exists():
        sample_proxies = [
            "http://proxy1.example.com:8080",
            "http://proxy2.example.com:8080",
            "socks5://proxy3.example.com:1080"
        ]
        
        with open(proxies_file, 'w') as f:
            f.write("\n".join(sample_proxies))
        
        print_colored("  Created sample proxies file", "32")
    
    print_colored("✅ Sample files created", "32")
    return True

def setup_telegram_bot():
    """Setup Telegram bot configuration"""
    print_colored("🤖 Setting up Telegram bot...", "36")
    
    config_file = Path("config.py")
    if config_file.exists():
        with open(config_file, 'r') as f:
            content = f.read()
        
        if "YOUR_BOT_TOKEN_HERE" in content:
            print_colored("⚠️  Please update TELEGRAM_BOT_TOKEN in config.py", "33")
            print_colored("   Get token from @BotFather on Telegram", "33")
        else:
            print_colored("✅ Telegram bot token configured", "32")
    
    return True

def setup_complete():
    """Display setup completion message"""
    print_colored("\n" + "="*60, "36")
    print_colored("🎉 SETUP COMPLETE!", "32")
    print_colored("="*60, "36")
    
    print_colored("\n🚀 To start VT View Tester:", "36")
    print_colored("   1. Terminal mode: python run.py --mode terminal", "33")
    print_colored("   2. Bot mode: python run.py --mode bot", "33")
    
    print_colored("\n📋 Next steps:", "36")
    print_colored("   • Add your accounts to data/accounts/accounts.json", "33")
    print_colored("   • Add proxies to data/proxies/proxies.txt", "33")
    print_colored("   • Configure Telegram bot token in config.py", "33")
    
    print_colored("\n⚠️  IMPORTANT:", "31")
    print_colored("   • Use only dummy accounts", "33")
    print_colored("   • Don't use real TikTok accounts", "33")
    print_colored("   • This is for educational purposes only", "33")
    
    print_colored("\n" + "="*60, "36")

def main():
    """Main setup function"""
    print_colored("\n" + "="*60, "36")
    print_colored("VT VIEW TESTER - SETUP", "36")
    print_colored("="*60, "36")
    
    # Check system
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Install Playwright
    if not install_playwright():
        return
    
    # Create directories
    if not create_directories():
        return
    
    # Initialize database
    if not initialize_database():
        return
    
    # Create sample files
    if not create_sample_files():
        return
    
    # Setup Telegram bot
    setup_telegram_bot()
    
    # Setup complete
    setup_complete()

if __name__ == "__main__":
    main()