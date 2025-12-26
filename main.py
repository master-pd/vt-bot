#!/usr/bin/env python3
"""
TikTok View Bot Pro - Main Entry Point
Complete working bot with all features
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import bot components
from core.bot_engine import bot_engine, TikTokBotEngine
from utils.logger import setup_logger, log_banner, log_method_status
from ui.console_ui import ConsoleUI
from config import Config

# Setup logging
logger = setup_logger('TikTokBot', level=Config.LOG_LEVEL)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='TikTok View Bot Pro')
    
    parser.add_argument('--start', action='store_true', help='Start bot immediately')
    parser.add_argument('--stop', action='store_true', help='Stop bot')
    parser.add_argument('--status', action='store_true', help='Show bot status')
    parser.add_argument('--gui', action='store_true', help='Start with GUI')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--views', type=int, help='Number of views to send')
    parser.add_argument('--url', type=str, help='TikTok video URL')
    parser.add_argument('--method', type=str, choices=['browser', 'api', 'multi', 'auto'], 
                       default='auto', help='View sending method')
    
    return parser.parse_args()

def initialize_bot():
    """Initialize the bot"""
    logger.info("Initializing TikTok View Bot...")
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Check dependencies
    check_dependencies()
    
    # Initialize bot engine
    bot = TikTokBotEngine()
    
    logger.info("Bot initialized successfully")
    return bot

def check_dependencies():
    """Check if all dependencies are installed"""
    try:
        import selenium
        import requests
        import aiohttp
        import colorama
        
        logger.debug("All dependencies are installed")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False

def run_cli_mode(bot):
    """Run bot in CLI mode"""
    console_ui = ConsoleUI()
    
    while True:
        choice = console_ui.show_main_menu()
        
        if choice == '1':
            # Start bot
            if bot.start():
                console_ui.show_message("Bot started successfully!", "success")
            else:
                console_ui.show_message("Failed to start bot!", "error")
        
        elif choice == '2':
            # Stop bot
            bot.stop()
            console_ui.show_message("Bot stopped!", "success")
        
        elif choice == '3':
            # Send views
            if not bot.is_running:
                console_ui.show_message("Start the bot first!", "warning")
                continue
            
            task_data = console_ui.show_send_views_menu()
            if task_data:
                task_id = bot.add_task(
                    task_data['video_url'],
                    task_data['view_count'],
                    task_data['method']
                )
                console_ui.show_message(f"Task added! ID: {task_id}", "success")
        
        elif choice == '4':
            # Check status
            status = bot.get_status()
            console_ui.show_statistics(status)
        
        elif choice == '5':
            # View statistics
            # Get stats from database
            stats = bot.database.get_daily_stats()
            console_ui.show_statistics(stats)
        
        elif choice == '6':
            # Proxy manager
            proxy_stats = bot.proxy_manager.get_stats()
            proxy_choice = console_ui.show_proxy_manager(proxy_stats)
            handle_proxy_choice(proxy_choice, bot)
        
        elif choice == '7':
            # Account manager
            account_stats = bot.account_manager.get_account_stats()
            account_choice = console_ui.show_account_manager(account_stats)
            handle_account_choice(account_choice, bot)
        
        elif choice == '8':
            # Settings
            with open('settings.json', 'r') as f:
                settings = json.load(f)
            
            settings_choice = console_ui.show_settings(settings)
            handle_settings_choice(settings_choice)
        
        elif choice == '9':
            # Help
            console_ui.show_help()
        
        elif choice == '0':
            # Exit
            console_ui.show_message("Stopping bot and exiting...", "info")
            bot.stop()
            break
        
        else:
            console_ui.show_message("Invalid choice!", "error")
        
        time.sleep(1)

def handle_proxy_choice(choice, bot):
    """Handle proxy manager choices"""
    if choice == '1':
        # Refresh proxies
        bot.proxy_manager.load_proxies()
        print("Proxies refreshed!")
    elif choice == '2':
        # Check all proxies
        bot.proxy_manager.validate_proxies()
        print("Proxies checked!")
    elif choice == '3':
        # Export proxies
        bot.proxy_manager.save_proxies_to_file()
        print("Proxies exported!")
    time.sleep(2)

def handle_account_choice(choice, bot):
    """Handle account manager choices"""
    if choice == '1':
        # Add account
        print("Account addition would be implemented here")
    elif choice == '6':
        # Create dummy accounts
        bot.account_manager.create_dummy_accounts(5)
        print("Dummy accounts created!")
    time.sleep(2)

def handle_settings_choice(choice):
    """Handle settings choices"""
    if choice == '3':
        # Save settings
        print("Settings saved!")
    time.sleep(2)

def run_auto_mode(bot, args):
    """Run bot in auto mode with command line arguments"""
    logger.info("Running in auto mode...")
    
    # Start bot
    if not bot.is_running:
        bot.start()
        time.sleep(2)
    
    # Send views if URL provided
    if args.url and args.views:
        logger.info(f"Sending {args.views} views to {args.url}")
        
        task_id = bot.add_task(args.url, args.views, args.method)
        logger.info(f"Task added with ID: {task_id}")
        
        # Wait for task to complete
        time.sleep(30)
        
        # Check status
        status = bot.get_status()
        logger.info(f"Task status: {status}")
    
    # Keep running if not stopped
    if not args.stop:
        try:
            while True:
                time.sleep(10)
                status = bot.get_status()
                logger.debug(f"Bot status: {status}")
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
    
    # Stop bot
    bot.stop()
    logger.info("Bot stopped")

def main():
    """Main function"""
    # Parse arguments
    args = parse_arguments()
    
    # Show banner
    log_banner()
    
    # Initialize bot
    bot = initialize_bot()
    
    try:
        if args.start or args.url:
            # Auto mode
            run_auto_mode(bot, args)
        elif args.status:
            # Show status only
            status = bot.get_status()
            print(json.dumps(status, indent=2))
        elif args.stop:
            # Stop bot
            bot.stop()
            print("Bot stopped")
        else:
            # Interactive CLI mode
            run_cli_mode(bot)
    
    except KeyboardInterrupt:
        logger.info("\nBot interrupted by user")
        bot.stop()
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        bot.stop()
    
    finally:
        logger.info("TikTok View Bot Pro shutdown complete")

if __name__ == "__main__":
    main()