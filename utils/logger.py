"""
Advanced logging system for TikTok Bot
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
import colorama
from colorama import Fore, Style

colorama.init()

class ColoredFormatter(logging.Formatter):
    """Custom colored formatter for console output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        # Add color based on level
        color = self.COLORS.get(record.levelname, '')
        
        # Format message
        message = super().format(record)
        
        # Add color if not already present
        if color and not message.startswith('\x1b['):
            message = f"{color}{message}{Style.RESET_ALL}"
        
        return message

def setup_logger(
    name: str, 
    log_file: Optional[str] = None,
    level: str = "INFO",
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        console: Whether to show logs in console
    
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_bot_logger():
    """Get the main bot logger"""
    from config import Config
    
    # Create logs directory if not exists
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    
    # Generate log filename with date
    date_str = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(Config.LOG_DIR, f'bot_{date_str}.log')
    
    return setup_logger(
        'TikTokBot',
        log_file=log_file,
        level=Config.LOG_LEVEL,
        console=True
    )

class BotLogger:
    """Enhanced logger with additional features"""
    
    def __init__(self, name: str = "TikTokBot"):
        self.logger = setup_logger(name)
        self.session_start = datetime.now()
        self.stats = {
            'errors': 0,
            'warnings': 0,
            'views_sent': 0,
            'tasks_completed': 0
        }
    
    def log_start(self):
        """Log bot startup"""
        self.logger.info("=" * 50)
        self.logger.info("🚀 TikTok View Bot Starting")
        self.logger.info(f"📅 Session Start: {self.session_start}")
        self.logger.info("=" * 50)
    
    def log_stop(self):
        """Log bot shutdown"""
        duration = datetime.now() - self.session_start
        self.logger.info("=" * 50)
        self.logger.info("🛑 TikTok View Bot Stopping")
        self.logger.info(f"⏱️  Session Duration: {duration}")
        self.logger.info(f"📊 Stats: {self.stats}")
        self.logger.info("=" * 50)
    
    def log_view_sent(self, video_url: str, count: int, method: str):
        """Log successful view sending"""
        self.stats['views_sent'] += count
        self.logger.info(
            f"✅ Sent {count} views to {video_url} "
            f"(Method: {method}, Total: {self.stats['views_sent']})"
        )
    
    def log_error(self, error_msg: str, exception: Exception = None):
        """Log error with exception details"""
        self.stats['errors'] += 1
        
        if exception:
            self.logger.error(
                f"{error_msg}: {type(exception).__name__}: {str(exception)}"
            )
        else:
            self.logger.error(error_msg)
    
    def log_warning(self, warning_msg: str):
        """Log warning"""
        self.stats['warnings'] += 1
        self.logger.warning(warning_msg)
    
    def log_task_complete(self, task_id: str, result: dict):
        """Log task completion"""
        self.stats['tasks_completed'] += 1
        
        success = result.get('success_count', 0)
        total = result.get('requested_views', 0)
        
        if total > 0:
            rate = (success / total) * 100
            self.logger.info(
                f"📊 Task {task_id} Complete: "
                f"{success}/{total} ({rate:.1f}%) successful"
            )
    
    def log_proxy_status(self, active: int, total: int):
        """Log proxy status"""
        if total > 0:
            active_rate = (active / total) * 100
            self.logger.info(
                f"🌐 Proxies: {active}/{total} active ({active_rate:.1f}%)"
            )
    
    def log_account_status(self, active: int, total: int):
        """Log account status"""
        if total > 0:
            active_rate = (active / total) * 100
            self.logger.info(
                f"👤 Accounts: {active}/{total} active ({active_rate:.1f}%)"
            )
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return self.stats.copy()
    
    def save_stats(self, filepath: str = "logs/stats.json"):
        """Save statistics to file"""
        try:
            import json
            stats_data = {
                'session_start': self.session_start.isoformat(),
                'session_duration': str(datetime.now() - self.session_start),
                'stats': self.stats
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(stats_data, f, indent=2, default=str)
            
            self.logger.debug(f"Stats saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save stats: {e}")

# Global logger instance
bot_logger = BotLogger()

def log_banner():
    """Print ASCII art banner"""
    banner = f"""
{Fore.CYAN}{'='*60}
{Fore.GREEN}
▓█████▄  ██▓ ▄████▄   ██▓     ▒█████   █     █░▓█████  ██▀███  
▒██▀ ██▌▓██▒▒██▀ ▀█  ▓██▒    ▒██▒  ██▒▓█░ █ ░█░▓█   ▀ ▓██ ▒ ██▒
░██   █▌▒██▒▒▓█    ▄ ▒██░    ▒██░  ██▒▒█░ █ ░█ ▒███   ▓██ ░▄█ ▒
░▓█▄   ▌░██░▒▓▓▄ ▄██▒▒██░    ▒██   ██░░█░ █ ░█ ▒▓█  ▄ ▒██▀▀█▄  
░▒████▓ ░██░▒ ▓███▀ ░░██████▒░ ████▓▒░░░██▒██▓ ░▒████▒░██▓ ▒██▒
 ▒▒▓  ▒ ░▓  ░ ░▒ ▒  ░░ ▒░▓  ░░ ▒░▒░▒░ ░ ▓░▒ ▒  ░░ ▒░ ░░ ▒▓ ░▒▓░
 ░ ▒  ▒  ▒ ░  ░  ▒   ░ ░ ▒  ░  ░ ▒ ▒░   ▒ ░ ░   ░ ░  ░  ░▒ ░ ▒░
 ░ ░  ░  ▒ ░░          ░ ░   ░ ░ ░ ▒    ░   ░     ░     ░░   ░ 
   ░     ░  ░ ░          ░  ░    ░ ░      ░       ░  ░   ░     
 ░          ░                                                  
{Fore.CYAN}
╔══════════════════════════════════════════════════════════╗
║                TikTok View Bot Pro v2.5                  ║
║             Advanced View Automation System              ║
╚══════════════════════════════════════════════════════════╝
{Fore.RESET}
"""
    print(banner)

def log_method_status(methods: dict):
    """Log status of all methods"""
    from colorama import Fore, Style
    
    print(f"\n{Fore.CYAN}{'📊 Method Status':^60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    for method_name, method_data in methods.items():
        available = method_data.get('available', False)
        success_rate = method_data.get('success_rate', 0)
        views_sent = method_data.get('total_views_sent', 0)
        
        status_color = Fore.GREEN if available else Fore.RED
        status_text = "✅ AVAILABLE" if available else "❌ UNAVAILABLE"
        
        print(f"{Fore.WHITE}{method_name:20} {status_color}{status_text:15} "
              f"{Fore.YELLOW}Success: {success_rate:6.1f}%  "
              f"{Fore.CYAN}Views: {views_sent:,}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

# Export commonly used functions
__all__ = [
    'setup_logger',
    'get_bot_logger',
    'BotLogger',
    'bot_logger',
    'log_banner',
    'log_method_status'
]