"""
Telegram Bot - Remote control and notifications via Telegram
"""

import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

logger = logging.getLogger(__name__)

class TikTokTelegramBot:
    def __init__(self, token: str, bot_engine, authorized_users: list = None):
        self.token = token
        self.bot_engine = bot_engine
        self.authorized_users = authorized_users or []
        self.application = None
        self.is_running = False
        
        # Bot statistics
        self.stats = {
            'start_time': None,
            'total_commands': 0,
            'views_sent': 0,
            'active_tasks': 0
        }
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Check authorization
        if not self.is_authorized(user_id):
            await update.message.reply_text(
                "🚫 *Access Denied*\n\n"
                "You are not authorized to use this bot.",
                parse_mode='Markdown'
            )
            return
        
        # Welcome message
        welcome_text = """
🤖 *TikTok View Bot - Telegram Controller*

*Available Commands:*
/start - Show this message
/status - Check bot status
/views - Send views to video
/proxies - Manage proxies
/accounts - Manage accounts
/stats - Show statistics
/stop - Stop all tasks
/help - Show help

*Quick Actions:*
Use buttons below for quick access.
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data='status'),
                InlineKeyboardButton("🚀 Send Views", callback_data='send_views')
            ],
            [
                InlineKeyboardButton("🌐 Proxies", callback_data='proxies'),
                InlineKeyboardButton("👤 Accounts", callback_data='accounts')
            ],
            [
                InlineKeyboardButton("📈 Stats", callback_data='stats'),
                InlineKeyboardButton("🛑 Stop", callback_data='stop_all')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        self.stats['total_commands'] += 1
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        # Get bot status
        bot_status = self.bot_engine.get_status()
        
        status_text = f"""
📊 *Bot Status Report*

*General:*
• Status: {'✅ Running' if bot_status['running'] else '🛑 Stopped'}
• Active Tasks: {bot_status['active_tasks']}
• Queue Size: {bot_status['tasks_in_queue']}
• Completed Tasks: {bot_status['completed_tasks']}

*Resources:*
• Proxies: {bot_status.get('proxies_available', 0)}
• Accounts: {bot_status.get('accounts_available', 0)}

*Statistics:*
• Total Views Sent: {bot_status['stats'].get('total_views_sent', 0):,}
• Successful Views: {bot_status['stats'].get('successful_views', 0):,}
• Failed Views: {bot_status['stats'].get('failed_views', 0):,}
• Uptime: {self.get_uptime()}
        """
        
        await update.message.reply_text(
            status_text,
            parse_mode='Markdown'
        )
        
        self.stats['total_commands'] += 1
    
    async def views_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /views command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        # Check if bot is running
        if not self.bot_engine.is_running:
            await update.message.reply_text(
                "❌ *Bot is not running*\n\n"
                "Start the bot first using /start_bot",
                parse_mode='Markdown'
            )
            return
        
        # Ask for video URL
        await update.message.reply_text(
            "📹 *Send Video URL*\n\n"
            "Please send the TikTok video URL you want to send views to.",
            parse_mode='Markdown'
        )
        
        # Set next handler
        context.user_data['expecting'] = 'video_url'
        
        self.stats['total_commands'] += 1
    
    async def handle_video_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video URL input"""
        video_url = update.message.text
        
        # Validate URL
        if not self.is_valid_tiktok_url(video_url):
            await update.message.reply_text(
                "❌ *Invalid URL*\n\n"
                "Please send a valid TikTok video URL.",
                parse_mode='Markdown'
            )
            return
        
        # Store URL and ask for view count
        context.user_data['video_url'] = video_url
        
        keyboard = [
            [
                InlineKeyboardButton("50", callback_data='views_50'),
                InlineKeyboardButton("100", callback_data='views_100'),
                InlineKeyboardButton("200", callback_data='views_200')
            ],
            [
                InlineKeyboardButton("500", callback_data='views_500'),
                InlineKeyboardButton("1000", callback_data='views_1000'),
                InlineKeyboardButton("Custom", callback_data='views_custom')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔢 *Select View Count*\n\n"
            "How many views would you like to send?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        context.user_data['expecting'] = 'view_count'
    
    async def handle_view_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle view count selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'views_custom':
            await query.edit_message_text(
                "✏️ *Enter Custom Amount*\n\n"
                "Please enter the number of views to send:",
                parse_mode='Markdown'
            )
            context.user_data['expecting'] = 'custom_views'
            return
        
        # Parse view count from callback
        view_count = int(query.data.split('_')[1])
        
        # Ask for method selection
        context.user_data['view_count'] = view_count
        
        keyboard = [
            [
                InlineKeyboardButton("🌐 Browser", callback_data='method_browser'),
                InlineKeyboardButton("⚡ API", callback_data='method_api')
            ],
            [
                InlineKeyboardButton("👥 Multi-Account", callback_data='method_multi'),
                InlineKeyboardButton("🤖 AI Optimized", callback_data='method_ai')
            ],
            [
                InlineKeyboardButton("🔄 Auto", callback_data='method_auto'),
                InlineKeyboardButton("📊 Hybrid", callback_data='method_hybrid')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *Select Method*\n\n"
            "Choose the method to send views:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        context.user_data['expecting'] = 'method'
    
    async def handle_method_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle method selection"""
        query = update.callback_query
        await query.answer()
        
        method_map = {
            'method_browser': 'browser',
            'method_api': 'api',
            'method_multi': 'multi_account',
            'method_ai': 'ai_optimized',
            'method_auto': 'auto',
            'method_hybrid': 'hybrid'
        }
        
        method = method_map.get(query.data, 'auto')
        
        # Get stored data
        video_url = context.user_data.get('video_url')
        view_count = context.user_data.get('view_count')
        
        if not video_url or not view_count:
            await query.edit_message_text("❌ Error: Missing data")
            return
        
        # Confirm task
        context.user_data['method'] = method
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data='confirm_task'),
                InlineKeyboardButton("❌ Cancel", callback_data='cancel_task')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📋 *Task Summary*\n\n"
            f"• Video: {video_url[:50]}...\n"
            f"• Views: {view_count:,}\n"
            f"• Method: {method}\n\n"
            f"*Confirm to start?*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def confirm_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and start task"""
        query = update.callback_query
        await query.answer()
        
        # Get task data
        video_url = context.user_data.get('video_url')
        view_count = context.user_data.get('view_count')
        method = context.user_data.get('method', 'auto')
        
        # Add task to bot
        task_id = self.bot_engine.add_task(video_url, view_count, method)
        
        # Clear user data
        context.user_data.clear()
        
        await query.edit_message_text(
            f"✅ *Task Started*\n\n"
            f"Task ID: `{task_id}`\n"
            f"Views: {view_count:,}\n"
            f"Method: {method}\n\n"
            f"Use /status to monitor progress.",
            parse_mode='Markdown'
        )
        
        self.stats['views_sent'] += view_count
        self.stats['active_tasks'] += 1
    
    async def proxies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /proxies command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        # Get proxy stats
        proxy_stats = self.bot_engine.proxy_manager.get_stats()
        
        proxy_text = f"""
🌐 *Proxy Manager*

*Statistics:*
• Total Proxies: {proxy_stats.get('total_proxies', 0):,}
• Active Proxies: {proxy_stats.get('active_proxies', 0):,}
• Inactive Proxies: {proxy_stats.get('inactive_proxies', 0):,}
• Success Rate: {proxy_stats.get('success_rate', 0)*100:.1f}%
• Avg Response Time: {proxy_stats.get('average_response_time', 0):.2f}s

*Actions:*
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data='refresh_proxies'),
                InlineKeyboardButton("✅ Check All", callback_data='check_proxies')
            ],
            [
                InlineKeyboardButton("📊 Top 10", callback_data='top_proxies'),
                InlineKeyboardButton("🗑️ Cleanup", callback_data='cleanup_proxies')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            proxy_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        self.stats['total_commands'] += 1
    
    async def accounts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /accounts command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        # Get account stats
        account_stats = self.bot_engine.account_manager.get_account_stats()
        
        account_text = f"""
👤 *Account Manager*

*Statistics:*
• Total Accounts: {account_stats.get('total_accounts', 0):,}
• Active Accounts: {account_stats.get('active_accounts', 0):,}
• Inactive Accounts: {account_stats.get('inactive_accounts', 0):,}
• Total Views: {account_stats.get('total_views', 0):,}
• Avg Success Rate: {account_stats.get('average_success_rate', 0)*100:.1f}%

*Actions:*
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data='refresh_accounts'),
                InlineKeyboardButton("✅ Check All", callback_data='check_accounts')
            ],
            [
                InlineKeyboardButton("➕ Add Account", callback_data='add_account'),
                InlineKeyboardButton("🤖 Create Dummy", callback_data='create_dummy')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            account_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        self.stats['total_commands'] += 1
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        # Get bot stats
        bot_stats = self.bot_engine.get_status()['stats']
        
        stats_text = f"""
📈 *Bot Statistics*

*Performance:*
• Total Views Sent: {bot_stats.get('total_views_sent', 0):,}
• Successful Views: {bot_stats.get('successful_views', 0):,}
• Failed Views: {bot_stats.get('failed_views', 0):,}
• Success Rate: {(bot_stats.get('successful_views', 0)/max(bot_stats.get('total_views_sent', 1), 1))*100:.1f}%

*Telegram Bot:*
• Commands Processed: {self.stats['total_commands']:,}
• Views Sent via TG: {self.stats['views_sent']:,}
• Active Tasks: {self.stats['active_tasks']}
• Uptime: {self.get_uptime()}

*Session:*
• Start Time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S') if self.stats['start_time'] else 'N/A'}
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown'
        )
        
        self.stats['total_commands'] += 1
    
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        keyboard = [
            [
                InlineKeyboardButton("🛑 Stop Bot", callback_data='stop_bot'),
                InlineKeyboardButton("🗑️ Stop All Tasks", callback_data='stop_tasks')
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data='cancel_stop')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *Stop Operations*\n\n"
            "Select what you want to stop:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        self.stats['total_commands'] += 1
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access Denied")
            return
        
        help_text = """
📚 *TikTok View Bot - Help Guide*

*Basic Commands:*
/start - Start the bot and show menu
/status - Check bot status
/views - Send views to TikTok video
/proxies - Manage proxy list
/accounts - Manage TikTok accounts
/stats - Show statistics
/stop - Stop operations
/help - This help message

*How to Send Views:*
1. Use /views command
2. Send TikTok video URL
3. Select view count
4. Choose method
5. Confirm task

*Methods Explained:*
• Browser - Most reliable, uses real browser
• API - Fast but less reliable
• Multi-Account - Uses multiple accounts
• AI Optimized - Smart method selection
• Auto - Bot chooses best method
• Hybrid - Combines multiple methods

*Need Help?*
Contact the administrator for support.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
        
        self.stats['total_commands'] += 1
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        # Handle different callbacks
        if callback_data == 'status':
            await self.status_command(update, context)
        elif callback_data == 'send_views':
            await self.views_command(update, context)
        elif callback_data == 'proxies':
            await self.proxies_command(update, context)
        elif callback_data == 'accounts':
            await self.accounts_command(update, context)
        elif callback_data == 'stats':
            await self.stats_command(update, context)
        elif callback_data == 'stop_all':
            await self.stop_command(update, context)
        elif callback_data.startswith('views_'):
            await self.handle_view_count(update, context)
        elif callback_data.startswith('method_'):
            await self.handle_method_selection(update, context)
        elif callback_data == 'confirm_task':
            await self.confirm_task(update, context)
        elif callback_data == 'cancel_task':
            await query.edit_message_text("❌ Task cancelled")
            context.user_data.clear()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            return
        
        # Check what we're expecting
        expecting = context.user_data.get('expecting')
        
        if expecting == 'video_url':
            await self.handle_video_url(update, context)
        elif expecting == 'custom_views':
            try:
                view_count = int(update.message.text)
                if view_count <= 0 or view_count > 10000:
                    await update.message.reply_text("Please enter a number between 1 and 10000")
                    return
                
                context.user_data['view_count'] = view_count
                await self.handle_view_count(update, context)
            except ValueError:
                await update.message.reply_text("Please enter a valid number")
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        if not self.authorized_users:  # If empty, allow all
            return True
        return user_id in self.authorized_users
    
    def is_valid_tiktok_url(self, url: str) -> bool:
        """Validate TikTok URL"""
        tiktok_domains = [
            'tiktok.com',
            'vt.tiktok.com',
            'vm.tiktok.com'
        ]
        
        return any(domain in url for domain in tiktok_domains)
    
    def get_uptime(self) -> str:
        """Get bot uptime as string"""
        if not self.stats['start_time']:
            return "Not started"
        
        delta = datetime.now() - self.stats['start_time']
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    async def send_notification(self, chat_id: int, message: str, parse_mode: str = 'Markdown'):
        """Send notification to chat"""
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def task_completed_notification(self, task_id: str, result: Dict):
        """Send task completed notification"""
        success = result.get('success', False)
        views_sent = result.get('views_sent', 0)
        time_taken = result.get('time_taken', 0)
        
        emoji = "✅" if success else "❌"
        status = "Completed" if success else "Failed"
        
        message = f"""
{emoji} *Task {status}*

*Task ID:* `{task_id}`
*Status:* {status}
*Views Sent:* {views_sent:,}
*Time Taken:* {time_taken:.1f}s

*Details:*
{result.get('details', 'No details')}
        """
        
        # Send to all authorized users
        for user_id in self.authorized_users:
            await self.send_notification(user_id, message)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Telegram bot error: {context.error}")
        
        try:
            if update and update.effective_user:
                await update.effective_user.send_message(
                    "❌ An error occurred. Please try again."
                )
        except:
            pass
    
    def start(self):
        """Start the Telegram bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CommandHandler("views", self.views_command))
            self.application.add_handler(CommandHandler("proxies", self.proxies_command))
            self.application.add_handler(CommandHandler("accounts", self.accounts_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("stop", self.stop_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            # Start bot
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("Telegram bot started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the Telegram bot"""
        if self.application:
            self.application.stop()
            self.is_running = False
            logger.info("Telegram bot stopped")