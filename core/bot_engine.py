"""
Main Bot Engine - Coordinates all components
"""

import asyncio
import threading
import time
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from queue import Queue

from core.view_sender import ViewSender
from core.proxy_manager import ProxyManager
from core.account_manager import AccountManager
from methods.method_executor import MethodExecutor
from utils.logger import setup_logger
from database.database_manager import DatabaseManager

logger = setup_logger(__name__)

class TikTokBotEngine:
    def __init__(self):
        self.config = self.load_config()
        self.is_running = False
        self.active_tasks = []
        self.task_queue = Queue()
        self.results = []
        
        # Initialize managers
        self.proxy_manager = ProxyManager()
        self.account_manager = AccountManager()
        self.method_executor = MethodExecutor()
        self.database = DatabaseManager()
        self.view_sender = ViewSender()
        
        # Statistics
        self.stats = {
            'total_views_sent': 0,
            'successful_views': 0,
            'failed_views': 0,
            'start_time': None,
            'last_activity': None
        }
    
    def load_config(self):
        """Load configuration from settings.json"""
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("settings.json not found, using defaults")
            return self.get_default_config()
    
    def get_default_config(self):
        """Default configuration"""
        return {
            'bot': {
                'max_threads': 10,
                'auto_start': True
            },
            'views': {
                'default_count': 100,
                'min_per_batch': 10
            }
        }
    
    def start(self):
        """Start the bot engine"""
        if self.is_running:
            logger.warning("Bot is already running")
            return False
        
        logger.info("🚀 Starting TikTok View Bot...")
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # Initialize components
        self.initialize_components()
        
        # Start background tasks
        self.start_background_tasks()
        
        logger.info("✅ Bot started successfully")
        return True
    
    def initialize_components(self):
        """Initialize all bot components"""
        logger.info("Initializing components...")
        
        # Load proxies
        proxy_count = self.proxy_manager.load_proxies()
        logger.info(f"Loaded {proxy_count} proxies")
        
        # Load accounts
        account_count = self.account_manager.load_accounts()
        logger.info(f"Loaded {account_count} accounts")
        
        # Initialize database
        self.database.initialize()
        
        logger.info("Components initialized")
    
    def start_background_tasks(self):
        """Start background maintenance tasks"""
        # Proxy checker
        proxy_thread = threading.Thread(
            target=self.proxy_manager.background_checker,
            daemon=True
        )
        proxy_thread.start()
        
        # Stats updater
        stats_thread = threading.Thread(
            target=self.update_stats_periodically,
            daemon=True
        )
        stats_thread.start()
        
        # Task processor
        processor_thread = threading.Thread(
            target=self.process_task_queue,
            daemon=True
        )
        processor_thread.start()
        
        logger.info("Background tasks started")
    
    def update_stats_periodically(self):
        """Update statistics periodically"""
        while self.is_running:
            time.sleep(60)  # Update every minute
            self.save_stats()
    
    def save_stats(self):
        """Save current statistics"""
        stats_file = 'logs/stats.json'
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
    
    def process_task_queue(self):
        """Process tasks from queue"""
        while self.is_running:
            try:
                if not self.task_queue.empty():
                    task = self.task_queue.get()
                    self.execute_task(task)
                else:
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Error processing task: {e}")
    
    def execute_task(self, task: Dict):
        """Execute a single view task"""
        task_id = task.get('id', 'unknown')
        logger.info(f"Executing task {task_id}")
        
        try:
            result = self.view_sender.send_views(
                video_url=task['video_url'],
                view_count=task['view_count'],
                method=task.get('method', 'auto')
            )
            
            if result['success']:
                self.stats['successful_views'] += result['views_sent']
                logger.info(f"✅ Task {task_id} completed: {result['views_sent']} views sent")
            else:
                self.stats['failed_views'] += task['view_count']
                logger.warning(f"❌ Task {task_id} failed: {result['error']}")
            
            # Update database
            self.database.save_task_result(task_id, result)
            
            # Add to results
            self.results.append({
                'task_id': task_id,
                'result': result,
                'timestamp': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
    
    def add_task(self, video_url: str, view_count: int, method: str = "auto"):
        """Add a new view task"""
        task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
        
        task = {
            'id': task_id,
            'video_url': video_url,
            'view_count': view_count,
            'method': method,
            'added_at': datetime.now()
        }
        
        self.task_queue.put(task)
        logger.info(f"Added task {task_id}: {view_count} views to {video_url}")
        
        return task_id
    
    def stop(self):
        """Stop the bot engine gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping TikTok View Bot...")
        self.is_running = False
        
        # Wait for tasks to complete
        time.sleep(5)
        
        # Save final stats
        self.save_stats()
        
        # Close components
        self.database.close()
        
        logger.info("✅ Bot stopped successfully")
    
    def get_status(self):
        """Get current bot status"""
        return {
            'running': self.is_running,
            'tasks_in_queue': self.task_queue.qsize(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.results),
            'stats': self.stats,
            'proxies_available': len(self.proxy_manager.active_proxies),
            'accounts_available': len(self.account_manager.active_accounts)
        }
    
    def emergency_stop(self):
        """Emergency stop all activities"""
        logger.warning("🆘 EMERGENCY STOP INITIATED!")
        self.is_running = False
        
        # Kill all threads
        for task in self.active_tasks:
            if hasattr(task, 'stop'):
                task.stop()
        
        # Clear queue
        while not self.task_queue.empty():
            self.task_queue.get()
        
        logger.info("🛑 All activities stopped")

# Single instance
bot_engine = TikTokBotEngine()