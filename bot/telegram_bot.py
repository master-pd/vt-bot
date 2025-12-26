"""
Telegram Bot Handler
Professional Telegram Bot Interface
"""

import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

from utils.logger import setup_logger
from core.engine import ViewEngine
from config import TELEGRAM_BOT_TOKEN, PROJECT_NAME, VERSION

logger = setup_logger(__name__)

class TelegramBot:
    """Telegram bot handler"""
    
    def __init__(self):
        self.engine = None
        self.application = None
        
    async def initialize(self):
        """Initialize bot"""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            self.engine = ViewEngine()
            await self.engine.initialize()
            
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
            
            # Add handlers
            self.add_handlers()
            
            logger.info("Telegram bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def add_handlers(self):
        """Add command handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("test", self.test_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
    
    async def safe_reply(self, update: Update, text: str, **kwargs):
        """Reply safely, whether message or callback query"""
        if update.message:
            await update.message.reply_text(text, **kwargs)
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(text, **kwargs)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_message = f"""
🚀 *Welcome to {PROJECT_NAME}!* 🚀

*Version:* {VERSION}
*Your ID:* `{user.id}`

*Available Commands:*
/start - Start the bot
/help - Show help
/stats - View statistics
/test - Start a view test

Send me a TikTok URL to start sending views!
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Statistics", callback_data="stats"),
                InlineKeyboardButton("🚀 Start Test", callback_data="test")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.safe_reply(update, welcome_message, parse_mode="Markdown", reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
*🤖 How to Use VT View Tester Bot*

1. *Send TikTok URL* - Just send me any TikTok video URL
2. *Set View Count* - I'll ask how many views you want
3. *Start Test* - I'll begin sending views immediately

*Commands:*
• /start - Start the bot
• /help - Show this help
• /stats - View statistics
• /test - Start a new test

*Features:*
• 🚀 Fast view sending
• 🔒 Proxy rotation
• 📊 Real-time statistics
• ⚡ Asynchronous processing

*Note:* Use dummy accounts only!
        """
        
        await self.safe_reply(update, help_text, parse_mode="Markdown")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        if not self.engine:
            await self.safe_reply(update, "❌ Engine not initialized")
            return
        
        stats = self.engine.get_stats()
        
        stats_text = f"""
*📊 System Statistics*

*Total Views Sent:* `{stats['total_views_sent']:,}`
*Total Views Failed:* `{stats['total_views_failed']:,}`
*Active Tasks:* `{stats['active_tasks']}`
*Available Proxies:* `{stats['available_proxies']}`
*Requests/Minute:* `{stats['requests_per_minute']:.1f}`
*Status:* {'🟢 Running' if stats['running'] else '🔴 Stopped'}
        """
        
        await self.safe_reply(update, stats_text, parse_mode="Markdown")
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        await self.safe_reply(
            update,
            "🎬 Please send me the TikTok video URL you want to send views to:",
            parse_mode="Markdown"
        )
        context.user_data['awaiting_url'] = True
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        text = update.message.text if update.message else ""

        if context.user_data.get('awaiting_url'):
            # User is sending URL
            await self.handle_url_input(update, context, text)
        elif context.user_data.get('awaiting_count'):
            # User is sending view count
            await self.handle_view_count(update, context, text)
        elif 'tiktok.com' in text.lower():
            # User sent a TikTok URL directly
            await self.handle_tiktok_url(update, context, text)
        else:
            await self.safe_reply(
                update,
                "❓ I didn't understand that. Send /help for instructions.",
                parse_mode="Markdown"
            )
    
    async def handle_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Handle URL input"""
        context.user_data['url'] = url
        context.user_data['awaiting_url'] = False
        context.user_data['awaiting_count'] = True
        
        await self.safe_reply(
            update,
            "🔢 How many views do you want to send? (Max: 10,000)",
            parse_mode="Markdown"
        )
    
    async def handle_view_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE, count_text: str):
        """Handle view count input"""
        try:
            count = int(count_text)
            if count < 1 or count > 10000:
                raise ValueError
            context.user_data['view_count'] = count
            context.user_data['awaiting_count'] = False

            # এখন তুমি engine থেকে view send করতে পারো
            await self.safe_reply(update, f"✅ Sending {count} views to your TikTok video now!")
            # উদাহরণ: await self.engine.send_views(context.user_data['url'], count)

        except ValueError:
            await self.safe_reply(update, "❌ Invalid number. Please send a number between 1 and 10,000.")

    async def handle_tiktok_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Handle TikTok URL directly"""
        context.user_data['url'] = url
        context.user_data['awaiting_count'] = True
        
        await self.safe_reply(
            update,
            f"✅ URL received!\n\n🔢 How many views do you want to send to this video? (Max: 10,000)",
            parse_mode="Markdown"
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "stats":
            await self.stats_command(update, context)
        elif data == "test":
            await self.test_command(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data == "settings":
            await self.safe_reply(update, "⚙️ Settings menu coming soon!")
    
    async def run(self):
        """Run the bot"""
        if not await self.initialize():
            return
        
        logger.info("Starting Telegram bot...")
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("Telegram bot started successfully")
            
            # Keep bot running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        if self.engine:
            await self.engine.shutdown()

async def start_bot():
    """Start the Telegram bot"""
    bot = TelegramBot()
    await bot.run()