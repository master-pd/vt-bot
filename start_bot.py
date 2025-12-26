#!/usr/bin/env python3
"""
VT View Tester - Telegram Bot Starter
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from bot.telegram_bot import start_bot
from utils.logger import setup_logger
from config import BANNER

logger = setup_logger(__name__)

async def main():
    """Main bot starter function"""
    print(BANNER)
    print("\n🚀 Starting VT View Tester Telegram Bot...\n")
    
    try:
        await start_bot()
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())