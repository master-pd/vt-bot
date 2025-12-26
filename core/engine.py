"""
View Engine - Core Processing System
"""

import asyncio
import aiohttp
import random
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from utils.logger import setup_logger
from utils.error_handler import handle_errors
from config import (
    MAX_CONCURRENT_REQUESTS,
    REQUEST_TIMEOUT,
    RETRY_ATTEMPTS,
    VIEWS_PER_MINUTE_LIMIT
)

logger = setup_logger(__name__)

@dataclass
class ViewTask:
    """View task data class"""
    video_url: str
    view_count: int
    task_id: str
    created_at: datetime
    status: str = "pending"
    views_sent: int = 0
    views_failed: int = 0
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "video_url": self.video_url,
            "view_count": self.view_count,
            "views_sent": self.views_sent,
            "views_failed": self.views_failed,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

class ViewEngine:
    """Main view sending engine"""
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.active_tasks: Dict[str, ViewTask] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxies: List[str] = []
        self.accounts: List[Dict] = []
        self.running = False
        self.stats = {
            "total_views_sent": 0,
            "total_views_failed": 0,
            "start_time": None,
            "requests_per_minute": 0
        }
    
    async def initialize(self):
        """Initialize the engine"""
        logger.info("Initializing View Engine...")
        
        # Create aiohttp session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        )
        
        # Load proxies and accounts
        await self.load_proxies()
        await self.load_accounts()
        
        self.stats["start_time"] = time.time()
        self.running = True
        
        logger.info("View Engine initialized successfully")
    
    async def load_proxies(self):
        """Load proxies from file"""
        try:
            from utils.file_handler import read_lines
            proxy_file = "data/proxies/proxies.txt"
            self.proxies = await read_lines(proxy_file)
            logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            logger.warning(f"Could not load proxies: {e}")
            self.proxies = []
    
    async def load_accounts(self):
        """Load accounts from file"""
        try:
            from utils.file_handler import read_json
            accounts_file = "data/accounts/accounts.json"
            self.accounts = await read_json(accounts_file)
            logger.info(f"Loaded {len(self.accounts)} accounts")
        except Exception as e:
            logger.warning(f"Could not load accounts: {e}")
            self.accounts = []
    
    @handle_errors
    async def send_view(self, video_url: str, proxy: str = None) -> bool:
        """Send a single view to video URL"""
        if not self.session:
            return False
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        try:
            async with self.semaphore:
                if proxy:
                    connector = aiohttp.TCPConnector(ssl=False)
                else:
                    connector = None
                
                async with self.session.get(
                    video_url,
                    headers=headers,
                    proxy=proxy,
                    connector=connector,
                    allow_redirects=True
                ) as response:
                    # Check if request was successful
                    if response.status == 200:
                        # Simulate view watching (you can add actual video watching logic)
                        await asyncio.sleep(random.uniform(3, 10))
                        return True
                    else:
                        logger.warning(f"Request failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.debug(f"View sending failed: {e}")
            return False
    
    async def process_task(self, task: ViewTask):
        """Process a view task"""
        logger.info(f"Processing task {task.task_id}: {task.view_count} views to {task.video_url}")
        
        task.status = "processing"
        successful_views = 0
        
        for i in range(task.view_count):
            if not self.running:
                break
            
            # Rotate proxy
            proxy = random.choice(self.proxies) if self.proxies else None
            
            # Send view
            success = await self.send_view(task.video_url, proxy)
            
            if success:
                successful_views += 1
                task.views_sent += 1
                self.stats["total_views_sent"] += 1
            else:
                task.views_failed += 1
                self.stats["total_views_failed"] += 1
            
            # Update stats
            self.update_request_rate()
            
            # Progress update every 10 views
            if (i + 1) % 10 == 0:
                logger.info(f"Task {task.task_id}: {i+1}/{task.view_count} views sent")
            
            # Rate limiting
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        task.status = "completed"
        logger.info(f"Task {task.task_id} completed: {successful_views}/{task.view_count} successful")
        
        return successful_views
    
    def update_request_rate(self):
        """Update requests per minute rate"""
        current_time = time.time()
        elapsed_minutes = (current_time - self.stats["start_time"]) / 60
        
        if elapsed_minutes > 0:
            total_requests = self.stats["total_views_sent"] + self.stats["total_views_failed"]
            self.stats["requests_per_minute"] = total_requests / elapsed_minutes
    
    async def create_task(self, video_url: str, view_count: int) -> str:
        """Create a new view task"""
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        task = ViewTask(
            video_url=video_url,
            view_count=view_count,
            task_id=task_id,
            created_at=datetime.now()
        )
        
        self.active_tasks[task_id] = task
        
        # Start processing in background
        asyncio.create_task(self.process_task(task))
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        task = self.active_tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            **self.stats,
            "active_tasks": len(self.active_tasks),
            "available_proxies": len(self.proxies),
            "available_accounts": len(self.accounts),
            "running": self.running
        }
    
    async def shutdown(self):
        """Shutdown the engine"""
        logger.info("Shutting down View Engine...")
        self.running = False
        
        # Cancel all tasks
        for task_id in list(self.active_tasks.keys()):
            task = self.active_tasks[task_id]
            if task.status == "processing":
                task.status = "cancelled"
        
        # Close session
        if self.session:
            await self.session.close()
        
        logger.info("View Engine shutdown complete")