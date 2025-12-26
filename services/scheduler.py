"""
Task Scheduler Service
Advanced scheduling system for periodic tasks
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass

from utils.logger import setup_logger
from database.crud import cleanup_old_data, create_log
from database.models import SessionLocal
from utils.file_handler import backup_database

logger = setup_logger(__name__)

@dataclass
class ScheduledTask:
    """Scheduled task configuration"""
    name: str
    function: Callable
    interval: str  # 'hourly', 'daily', 'weekly', or cron-like
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    last_run: Optional[datetime] = None
    enabled: bool = True

class TaskScheduler:
    """Advanced task scheduler"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.schedule_thread = None
        
    def add_task(
        self,
        name: str,
        function: Callable,
        interval: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        enabled: bool = True
    ):
        """Add a scheduled task"""
        task = ScheduledTask(
            name=name,
            function=function,
            interval=interval,
            args=args or [],
            kwargs=kwargs or {},
            enabled=enabled
        )
        
        self.tasks[name] = task
        logger.info(f"Added scheduled task: {name} ({interval})")
        
    def remove_task(self, name: str):
        """Remove a scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed scheduled task: {name}")
    
    def enable_task(self, name: str):
        """Enable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            logger.info(f"Enabled task: {name}")
    
    def disable_task(self, name: str):
        """Disable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            logger.info(f"Disabled task: {name}")
    
    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Task scheduler started")
        
        # Add default tasks
        self._add_default_tasks()
        
        # Start scheduling loop
        asyncio.create_task(self._scheduler_loop())
        
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    def _add_default_tasks(self):
        """Add default system tasks"""
        # Daily database backup at 2 AM
        self.add_task(
            name="daily_backup",
            function=self._backup_database,
            interval="02:00",
            enabled=True
        )
        
        # Hourly proxy validation
        self.add_task(
            name="validate_proxies",
            function=self._validate_proxies,
            interval="hourly",
            enabled=True
        )
        
        # Daily data cleanup at 3 AM
        self.add_task(
            name="cleanup_data",
            function=self._cleanup_old_data,
            interval="03:00",
            kwargs={"days": 30},
            enabled=True
        )
        
        # Account status check every 6 hours
        self.add_task(
            name="check_accounts",
            function=self._check_account_status,
            interval="*/6",
            enabled=True
        )
        
        # System health check every hour
        self.add_task(
            name="health_check",
            function=self._system_health_check,
            interval="hourly",
            enabled=True
        )
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                for task_name, task in self.tasks.items():
                    if not task.enabled:
                        continue
                    
                    # Check if it's time to run the task
                    if self._should_run_task(task, current_time):
                        await self._execute_task(task)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    def _should_run_task(self, task: ScheduledTask, current_time: datetime) -> bool:
        """Check if task should run"""
        if not task.last_run:
            return True
        
        if task.interval == "hourly":
            return current_time.hour != task.last_run.hour
        
        elif task.interval == "daily":
            return current_time.date() != task.last_run.date()
        
        elif task.interval == "weekly":
            return current_time.isocalendar()[1] != task.last_run.isocalendar()[1]
        
        elif ":" in task.interval:  # Time string like "02:00"
            try:
                scheduled_time = datetime.strptime(task.interval, "%H:%M").time()
                current_time_time = current_time.time()
                
                # Check if current time matches scheduled time
                # and we haven't run today yet
                if (current_time_time.hour == scheduled_time.hour and 
                    current_time_time.minute == scheduled_time.minute and
                    current_time.date() != task.last_run.date()):
                    return True
            except ValueError:
                pass
        
        elif task.interval.startswith("*/"):  # Cron-like: "*/6" for every 6 hours
            try:
                interval_hours = int(task.interval[2:])
                hours_diff = (current_time - task.last_run).total_seconds() / 3600
                return hours_diff >= interval_hours
            except (ValueError, IndexError):
                pass
        
        return False
    
    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        logger.info(f"Executing scheduled task: {task.name}")
        
        try:
            if asyncio.iscoroutinefunction(task.function):
                result = await task.function(*task.args, **task.kwargs)
            else:
                # Run sync function in executor
                result = await asyncio.get_event_loop().run_in_executor(
                    None, task.function, *task.args, **task.kwargs
                )
            
            task.last_run = datetime.now()
            logger.info(f"Task {task.name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing task {task.name}: {e}")
            
            # Log error to database
            db = SessionLocal()
            try:
                create_log(db, "error", "scheduler", f"Task {task.name} failed: {str(e)}")
                db.commit()
            except Exception as db_error:
                logger.error(f"Failed to log error to database: {db_error}")
            finally:
                db.close()
    
    # Default task implementations
    async def _backup_database(self):
        """Backup database task"""
        logger.info("Running scheduled database backup...")
        
        try:
            success = await backup_database()
            if success:
                logger.info("Database backup completed successfully")
            else:
                logger.warning("Database backup failed")
        except Exception as e:
            logger.error(f"Database backup error: {e}")
    
    async def _validate_proxies(self):
        """Validate proxies task"""
        logger.info("Running scheduled proxy validation...")
        
        # This would implement proxy validation logic
        # For now, just log
        await asyncio.sleep(1)  # Simulate work
        logger.info("Proxy validation completed")
    
    async def _cleanup_old_data(self, days: int = 30):
        """Cleanup old data task"""
        logger.info(f"Running scheduled data cleanup (older than {days} days)...")
        
        db = SessionLocal()
        try:
            result = cleanup_old_data(db, days)
            logger.info(f"Data cleanup completed: {result}")
            db.commit()
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _check_account_status(self):
        """Check account status task"""
        logger.info("Running scheduled account status check...")
        
        # This would implement account status checking
        # For now, just log
        await asyncio.sleep(1)
        logger.info("Account status check completed")
    
    async def _system_health_check(self):
        """System health check task"""
        logger.info("Running scheduled system health check...")
        
        try:
            import psutil
            
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log to database
            db = SessionLocal()
            try:
                from database.models import SystemLog
                log_message = (
                    f"Health Check - CPU: {cpu_percent:.1f}%, "
                    f"RAM: {memory.percent:.1f}%, "
                    f"Disk: {disk.percent:.1f}%"
                )
                
                log = SystemLog(
                    level="info",
                    module="scheduler",
                    message=log_message
                )
                db.add(log)
                db.commit()
                
                logger.info(f"System health: {log_message}")
                
            except Exception as db_error:
                logger.error(f"Failed to log health check: {db_error}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        status_list = []
        
        for task_name, task in self.tasks.items():
            status_list.append({
                "name": task_name,
                "interval": task.interval,
                "enabled": task.enabled,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": self._calculate_next_run(task) if task.enabled else None
            })
        
        return status_list
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """Calculate next run time for task"""
        if not task.last_run:
            return datetime.now()
        
        current_time = datetime.now()
        
        if task.interval == "hourly":
            next_run = task.last_run + timedelta(hours=1)
            return next_run if next_run > current_time else current_time
        
        elif task.interval == "daily":
            next_run = task.last_run + timedelta(days=1)
            return next_run if next_run > current_time else current_time
        
        elif task.interval == "weekly":
            next_run = task.last_run + timedelta(weeks=1)
            return next_run if next_run > current_time else current_time
        
        elif ":" in task.interval:
            try:
                # Daily at specific time
                scheduled_time = datetime.strptime(task.interval, "%H:%M").time()
                next_run = datetime.combine(current_time.date(), scheduled_time)
                
                if next_run <= current_time:
                    next_run += timedelta(days=1)
                
                return next_run
            except ValueError:
                pass
        
        elif task.interval.startswith("*/"):
            try:
                interval_hours = int(task.interval[2:])
                next_run = task.last_run + timedelta(hours=interval_hours)
                return next_run if next_run > current_time else current_time
            except (ValueError, IndexError):
                pass
        
        return None
    
    async def run_task_now(self, task_name: str):
        """Run a task immediately"""
        if task_name not in self.tasks:
            logger.error(f"Task not found: {task_name}")
            return False
        
        task = self.tasks[task_name]
        
        if not task.enabled:
            logger.warning(f"Task {task_name} is disabled")
            return False
        
        logger.info(f"Manually executing task: {task_name}")
        
        try:
            await self._execute_task(task)
            return True
        except Exception as e:
            logger.error(f"Error manually executing task {task_name}: {e}")
            return False