"""
Professional Logging System
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config import LOGS_DIR, LOG_LEVEL, LOG_MAX_SIZE, LOG_BACKUP_COUNT, Colors

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Colors.BLUE,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.MAGENTA + Colors.BOLD
    }
    
    def format(self, record):
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Colors.RESET}"
        
        # Format message
        message = super().format(record)
        
        # Add timestamp with color
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colored_timestamp = f"{Colors.CYAN}{timestamp}{Colors.RESET}"
        
        return f"{colored_timestamp} {message}"

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    Setup a logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Custom log file path
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_formatter = ColoredFormatter(
        '%(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        log_path = LOGS_DIR / log_file if not Path(log_file).is_absolute() else Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

# Global logger instance
logger = setup_logger("VT_View_Tester", "vt_system.log")

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper

async def log_async_function_call(func):
    """Decorator to log async function calls"""
    async def wrapper(*args, **kwargs):
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"Error in async {func.__name__}: {e}")
            raise
    return wrapper