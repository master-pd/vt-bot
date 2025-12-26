#!/usr/bin/env python3
"""
VT View Tester - Main Application
Professional Production System
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import ViewEngine
from ui.terminal_ui import TerminalUI
from utils.logger import setup_logger
from config import BANNER, PROJECT_NAME, VERSION, AUTHOR

logger = setup_logger(__name__)

class VTViewTester:
    def __init__(self):
        self.engine = None
        self.ui = None
        self.running = False
        
    def print_banner(self):
        """Display stylish banner"""
        print(BANNER)
        print(f"{'='*60}")
        print(f"Project: {PROJECT_NAME}")
        print(f"Version: {VERSION}")
        print(f"Author: {AUTHOR}")
        print(f"{'='*60}")
        print()
        
    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("Initializing VT View Tester...")
            
            # Initialize engine
            self.engine = ViewEngine()
            await self.engine.initialize()
            
            # Initialize UI
            self.ui = TerminalUI(self.engine)
            
            logger.info("Initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def run_terminal_mode(self):
        """Run in terminal mode"""
        try:
            if not await self.initialize():
                return
            
            self.running = True
            await self.ui.run()
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Error in terminal mode: {e}")
        finally:
            await self.shutdown()
    
    async def run_bot_mode(self):
        """Run Telegram bot mode"""
        try:
            from bot.telegram_bot import start_bot
            await start_bot()
        except ImportError as e:
            logger.error(f"Telegram bot not available: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the system gracefully"""
        logger.info("Shutting down VT View Tester...")
        self.running = False
        
        if self.engine:
            await self.engine.shutdown()
        
        logger.info("Shutdown completed")
    
    def run(self, mode="terminal"):
        """Main run method"""
        self.print_banner()
        
        if mode == "terminal":
            asyncio.run(self.run_terminal_mode())
        elif mode == "bot":
            asyncio.run(self.run_bot_mode())
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: terminal, bot")

def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VT View Tester")
    parser.add_argument("--mode", choices=["terminal", "bot"], 
                       default="terminal", help="Run mode")
    parser.add_argument("--config", help="Config file path")
    
    args = parser.parse_args()
    
    # Create application instance
    app = VTViewTester()
    
    # Run application
    app.run(mode=args.mode)

if __name__ == "__main__":
    main()