"""
VT View Tester - Configuration File
Professional Production Ready
"""

import os
from pathlib import Path

# ==================== PROJECT INFO ====================
PROJECT_NAME = "VT View Tester Pro"
VERSION = "2.0.0"
AUTHOR = "MASTER (RANA)"
TEAM = "MAR PD"
LICENSE = "MIT"

# ==================== PATHS ====================
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
ACCOUNTS_DIR = DATA_DIR / "accounts"
PROXIES_DIR = DATA_DIR / "proxies"
BACKUP_DIR = DATA_DIR / "backups"

# Create directories
for directory in [DATA_DIR, LOGS_DIR, ACCOUNTS_DIR, PROXIES_DIR, BACKUP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== DATABASE ====================
DATABASE_NAME = "vt_database.db"
DATABASE_PATH = DATA_DIR / DATABASE_NAME

# ==================== BOT SETTINGS ====================
# Telegram Bot Token (set in environment or leave empty)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")

# ==================== VIEW ENGINE ====================
MAX_CONCURRENT_REQUESTS = 50
REQUEST_TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds
VIEWS_PER_MINUTE_LIMIT = 10000
SESSION_LIFETIME = 3600  # 1 hour in seconds

# ==================== PROXY SETTINGS ====================
PROXY_TIMEOUT = 10
MAX_PROXIES = 1000
PROXY_ROTATION_INTERVAL = 1  # Rotate every request
PROXY_TEST_URL = "http://www.tiktok.com"

# ==================== ACCOUNT SETTINGS ====================
MAX_ACCOUNTS = 1000
ACCOUNT_ROTATION_INTERVAL = 10  # Switch after 10 views
ACCOUNT_CHECK_INTERVAL = 3600  # 1 hour

# ==================== PERFORMANCE ====================
CPU_LIMIT = 80  # %
MEMORY_LIMIT = 85  # %
DISK_LIMIT = 90  # %

# ==================== LOGGING ====================
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "vt_system.log"
ERROR_LOG_FILE = LOGS_DIR / "vt_error.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ==================== UI SETTINGS ====================
UI_REFRESH_INTERVAL = 0.5  # seconds
PROGRESS_BAR_WIDTH = 50
TABLE_MAX_WIDTH = 100

# ==================== SECURITY ====================
ENABLE_RATE_LIMIT = True
RATE_LIMIT_PER_MINUTE = 1000
ENABLE_INPUT_VALIDATION = True

# ==================== COLOR CODES ====================
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BLACK = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

# ==================== BANNER ====================
BANNER = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██╗   ██╗████████╗    ██╗   ██╗██╗███████╗██╗    ██╗     ║
║     ██║   ██║╚══██╔══╝    ██║   ██║██║██╔════╝██║    ██║     ║
║     ██║   ██║   ██║       ██║   ██║██║█████╗  ██║ █╗ ██║     ║
║     ╚██╗ ██╔╝   ██║       ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║     ║
║      ╚████╔╝    ██║        ╚████╔╝ ██║███████╗╚███╔███╔╝     ║
║       ╚═══╝     ╚═╝         ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝      ║
║                                                              ║
║                 Σ  V I E W   T E S T E R                     ║
║                    Version: {VERSION}                        ║
║                    Author: {AUTHOR}                          ║
║                    Team: {TEAM}                              ║
║                                                              ║
╚═════════════════$══════════!══════════$══════════════════════╝
{Colors.RESET}
"""