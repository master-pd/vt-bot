"""
Configuration file for TikTok View Bot
"""

import json
import os
from datetime import datetime

class Config:
    # Application
    APP_NAME = "TikTok View Bot Pro"
    VERSION = "2.5.0"
    AUTHOR = "Anonymous"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    SCREENSHOT_DIR = os.path.join(TEMP_DIR, "screenshots")
    COOKIES_DIR = os.path.join(TEMP_DIR, "cookies")
    
    # Bot Settings
    MAX_CONCURRENT_TASKS = 5
    VIEWS_PER_HOUR_LIMIT = 1000
    VIEWS_PER_DAY_LIMIT = 5000
    
    # Time Settings (seconds)
    MIN_VIEW_TIME = 15
    MAX_VIEW_TIME = 60
    DELAY_BETWEEN_VIEWS = 2
    DELAY_BETWEEN_ACCOUNTS = 10
    
    # Proxy Settings
    PROXY_TIMEOUT = 15
    MAX_PROXY_RETRIES = 3
    PROXY_CHECK_INTERVAL = 3600  # 1 hour
    
    # Browser Settings
    HEADLESS = False
    WINDOW_WIDTH = 1920
    WINDOW_HEIGHT = 1080
    USER_AGENT_ROTATION = True
    
    # TikTok Settings
    TIKTOK_URL = "https://www.tiktok.com"
    TIKTOK_API_BASE = "https://api.tiktok.com"
    VIDEO_WATCH_PERCENTAGE = 0.7  # Watch 70% of video
    
    # Methods Priority
    METHODS_PRIORITY = [
        "browser_human",
        "mobile_emulation",
        "api_direct",
        "multi_account",
        "selenium_cloud",
        "websocket",
        "view_replay",
        "hybrid"
    ]
    
    # Success Thresholds
    MIN_SUCCESS_RATE = 70  # 70% views must register
    VERIFICATION_WAIT_TIME = 300  # 5 minutes for view update
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "bot.log"
    
    @classmethod
    def get_user_agents(cls):
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
    
    @classmethod
    def get_api_endpoints(cls):
        return {
            'view': f"{cls.TIKTOK_API_BASE}/api/item/detail/",
            'feed': f"{cls.TIKTOK_API_BASE}/api/recommend/item_list/",
            'share': f"{cls.TIKTOK_API_BASE}/api/share/item/",
            'like': f"{cls.TIKTOK_API_BASE}/api/item/like/",
            'comment': f"{cls.TIKTOK_API_BASE}/api/comment/post/"
        }
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        dirs = [cls.LOG_DIR, cls.TEMP_DIR, cls.SCREENSHOT_DIR, cls.COOKIES_DIR]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)