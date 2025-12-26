"""
VT ENGINE - Main Processing Engine
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from vt_config import config
from utils.vt_logger import VTLogger
from modules.vt_view_sender import VTViewSender
from modules.vt_account_manager import VTAccountManager
from modules.vt_proxy_manager import VTProxyManager
from modules.vt_bypass_system import VTBypassSystem

@dataclass
class ViewTask:
    """View task data class"""
    video_url: str
    view_count: int
    completed: int = 0
    failed: int = 0
    start_time: float = 0
    end_time: float = 0
    status: str = "pending"  # pending, running, completed, failed
    
    def progress(self) -> float:
        """Get task progress percentage"""
        if self.view_count == 0:
            return 0.0
        return (self.completed / self.view_count) * 100
    
    def remaining(self) -> int:
        """Get remaining views"""
        return self.view_count - self.completed
    
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time == 0:
            return 0.0
        if self.end_time > 0:
            return self.end_time - self.start_time
        return time.time() - self.start_time

class VTEngine:
    """Main VT Bot Engine"""
    
    def __init__(self):
        self.logger = VTLogger(__name__)
        self.config = config
        
        # Core modules
        self.view_sender = VTViewSender()
        self.account_manager = VTAccountManager()
        self.proxy_manager = VTProxyManager()
        self.bypass_system = VTBypassSystem()
        
        # Task management
        self.active_tasks: Dict[str, ViewTask] = {}
        self.task_queue = asyncio.Queue()
        self.running = False
        self.workers = []
        
        # Statistics
        self.stats = {
            "total_views_sent": 0,
            "successful_views": 0,
            "failed_views": 0,
            "total_tasks": 0,
            "active_tasks": 0,
            "avg_success_rate": 0.0,
            "start_time": time.time()
        }
        
        # Performance monitoring
        self.performance = {
            "views_per_minute": 0,
            "concurrent_workers": 0,
            "queue_size": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }
    
    async def initialize(self):
        """Initialize the engine"""
        try:
            self.logger.info("Initializing VT Engine...")
            
            # Initialize modules
            await self.account_manager.initialize()
            await self.proxy_manager.initialize()
            await self.view_sender.initialize()
            await self.bypass_system.initialize()
            
            # Start worker pool
            await self.start_workers()
            
            self.logger.success("VT Engine initialized successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Engine initialization failed: {e}")
            return False
    
    async def start_workers(self):
        """Start worker threads"""
        max_workers = self.config.get_max_concurrent()
        
        for i in range(max_workers):
            worker = asyncio.create_task(self.worker_task(f"Worker-{i+1}"))
            self.workers.append(worker)
        
        self.logger.info(f"Started {max_workers} workers")
    
    async def worker_task(self, worker_id: str):
        """Worker task for processing view requests"""
        while self.running:
            try:
                # Get task from queue
                task_data = await self.task_queue.get()
                
                if task_data is None:  # Shutdown signal
                    break
                
                task_id, video_url, views_needed = task_data
                
                # Process views
                await self.process_views(task_id, video_url, views_needed)
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_id} error: {e}")
    
    async def process_views(self, task_id: str, video_url: str, views_needed: int):
        """Process views for a task"""
        try:
            task = self.active_tasks.get(task_id)
            if not task:
                return
            
            views_sent = 0
            batch_size = min(50, views_needed)
            
            while views_sent < views_needed and self.running:
                # Get account and proxy
                account = await self.account_manager.get_account()
                proxy = await self.proxy_manager.get_proxy()
                
                if not account or not proxy:
                    await asyncio.sleep(1)
                    continue
                
                # Send views in batch
                batch_views = min(batch_size, views_needed - views_sent)
                success = await self.view_sender.send_views(
                    video_url=video_url,
                    account=account,
                    proxy=proxy,
                    view_count=batch_views
                )
                
                if success:
                    views_sent += batch_views
                    task.completed += batch_views
                    self.stats["successful_views"] += batch_views
                else:
                    task.failed += 1
                    self.stats["failed_views"] += 1
                
                # Update statistics
                self.update_statistics()
                
                # Add human-like delay
                if self.config.should_use_random_delays():
                    delay = random.uniform(
                        self.config.get_min_delay(),
                        self.config.get_max_delay()
                    )
                    await asyncio.sleep(delay)
                
                # Rotate account and proxy
                await self.account_manager.rotate_account(account)
                await self.proxy_manager.rotate_proxy(proxy)
            
            # Mark task as completed
            if views_sent >= views_needed:
                task.status = "completed"
                task.end_time = time.time()
                self.logger.success(f"Task {task_id} completed: {views_sent} views sent")
            else:
                task.status = "failed"
                self.logger.warning(f"Task {task_id} failed: {views_sent}/{views_needed} views sent")
                
        except Exception as e:
            self.logger.error(f"View processing error for task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = "failed"
    
    async def start_view_sending(self, video_url: str, view_count: int) -> str:
        """Start view sending task"""
        try:
            # Validate input
            if not self.validate_video_url(video_url):
                self.logger.error(f"Invalid video URL: {video_url}")
                return None
            
            if view_count < self.config.get_min_views() or view_count > self.config.get_max_views():
                self.logger.error(f"View count must be between {self.config.get_min_views()} and {self.config.get_max_views()}")
                return None
            
            # Create task
            task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
            task = ViewTask(
                video_url=video_url,
                view_count=view_count,
                start_time=time.time(),
                status="running"
            )
            
            # Add to active tasks
            self.active_tasks[task_id] = task
            self.stats["total_tasks"] += 1
            self.stats["active_tasks"] += 1
            
            # Add to queue in batches
            batch_size = 100
            for i in range(0, view_count, batch_size):
                batch_views = min(batch_size, view_count - i)
                await self.task_queue.put((task_id, video_url, batch_views))
            
            self.logger.info(f"Started task {task_id}: {view_count} views to {video_url}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Failed to start view sending: {e}")
            return None
    
    def validate_video_url(self, url: str) -> bool:
        """Validate TikTok video URL"""
        patterns = self.config.get_video_patterns()
        
        import re
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        
        return False
    
    def update_statistics(self):
        """Update engine statistics"""
        try:
            # Calculate success rate
            total = self.stats["successful_views"] + self.stats["failed_views"]
            if total > 0:
                self.stats["avg_success_rate"] = (self.stats["successful_views"] / total) * 100
            
            # Calculate views per minute
            elapsed = time.time() - self.stats["start_time"]
            if elapsed > 60:  # At least 1 minute
                self.performance["views_per_minute"] = (
                    self.stats["successful_views"] / (elapsed / 60)
                )
            
            # Update queue size
            self.performance["queue_size"] = self.task_queue.qsize()
            
            # Update worker count
            self.performance["concurrent_workers"] = len([
                w for w in self.workers if not w.done()
            ])
            
        except Exception as e:
            self.logger.error(f"Statistics update error: {e}")
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task_id,
            "video_url": task.video_url,
            "total_views": task.view_count,
            "completed": task.completed,
            "failed": task.failed,
            "progress": task.progress(),
            "remaining": task.remaining(),
            "elapsed_time": task.elapsed_time(),
            "status": task.status,
            "start_time": datetime.fromtimestamp(task.start_time).isoformat() if task.start_time > 0 else None,
            "end_time": datetime.fromtimestamp(task.end_time).isoformat() if task.end_time > 0 else None
        }
    
    async def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks"""
        tasks = []
        for task_id, task in self.active_tasks.items():
            tasks.append(await self.get_task_status(task_id))
        return tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.status = "cancelled"
        task.end_time = time.time()
        
        # Remove from queue (simplified)
        self.stats["active_tasks"] -= 1
        
        self.logger.info(f"Cancelled task {task_id}")
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        self.update_statistics()
        
        return {
            "engine_stats": self.stats,
            "performance": self.performance,
            "account_stats": await self.account_manager.get_statistics(),
            "proxy_stats": await self.proxy_manager.get_statistics(),
            "bypass_stats": await self.bypass_system.get_statistics(),
            "uptime": time.time() - self.stats["start_time"]
        }
    
    async def settings_menu(self):
        """Show settings menu"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        while True:
            choice = await terminal.show_settings_menu()
            
            if choice == "1":
                await self.configure_performance()
            elif choice == "2":
                await self.configure_security()
            elif choice == "3":
                await self.configure_proxy()
            elif choice == "4":
                await self.configure_anti_detection()
            elif choice == "5":
                await self.reset_settings()
            elif choice == "6":
                break
    
    async def configure_performance(self):
        """Configure performance settings"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        current = self.config.get_performance_settings()
        
        settings = await terminal.configure_performance(current)
        if settings:
            self.config.update({"performance": settings})
            self.logger.info("Performance settings updated")
    
    async def configure_security(self):
        """Configure security settings"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        current = self.config.get_security_settings()
        
        settings = await terminal.configure_security(current)
        if settings:
            self.config.update({"security": settings})
            self.logger.info("Security settings updated")
    
    async def configure_proxy(self):
        """Configure proxy settings"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        current = self.config.get("proxy", {})
        
        settings = await terminal.configure_proxy(current)
        if settings:
            self.config.update({"proxy": settings})
            self.logger.info("Proxy settings updated")
    
    async def configure_anti_detection(self):
        """Configure anti-detection settings"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        current = self.config.get_anti_detection_settings()
        
        settings = await terminal.configure_anti_detection(current)
        if settings:
            self.config.update({"anti_detection": settings})
            self.logger.info("Anti-detection settings updated")
    
    async def reset_settings(self):
        """Reset to default settings"""
        from ui.vt_terminal import VTTerminal
        terminal = VTTerminal()
        
        confirm = await terminal.confirm_action("Reset all settings to default?")
        if confirm:
            self.config.reset_to_default()
            self.logger.info("Settings reset to default")
    
    async def shutdown(self):
        """Shutdown the engine"""
        self.logger.info("Shutting down VT Engine...")
        
        self.running = False
        
        # Stop workers
        for _ in self.workers:
            await self.task_queue.put(None)
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Shutdown modules
        await self.view_sender.shutdown()
        await self.account_manager.shutdown()
        await self.proxy_manager.shutdown()
        await self.bypass_system.shutdown()
        
        self.logger.info("VT Engine shutdown complete")