#!/usr/bin/env python3
"""
VT View Tester - Run Script
Entry point for the application
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import VTViewTester
from database.models import init_database
from utils.logger import setup_logger

logger = setup_logger(__name__)

def initialize_system():
    """Initialize system components"""
    logger.info("Initializing VT View Tester system...")
    
    # Initialize database
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Check requirements
    check_dependencies()
    
    logger.info("System initialization complete")

def check_dependencies():
    """Check if all dependencies are available"""
    try:
        import aiohttp
        import sqlalchemy
        import telegram
        import colorama
        
        logger.info("All core dependencies are available")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="VT View Tester - Professional View Testing System"
    )
    
    parser.add_argument(
        "--mode",
        choices=["terminal", "bot", "server", "gui"],
        default="terminal",
        help="Run mode (default: terminal)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for web server (default: 5000)"
    )
    
    args = parser.parse_args()
    
    # Initialize system
    initialize_system()
    
    # Create and run application
    app = VTViewTester()
    
    if args.mode == "terminal":
        app.run(mode="terminal")
    elif args.mode == "bot":
        app.run(mode="bot")
    else:
        logger.error(f"Mode {args.mode} not implemented yet")
        sys.exit(1)

if __name__ == "__main__":
    main()