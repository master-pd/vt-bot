"""
Advanced Analytics Service
Real-time performance tracking and analysis
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

import aiofiles
from sqlalchemy.orm import Session

from utils.logger import setup_logger
from database.models import Test, TikTokAccount, Proxy, SystemLog
from config import DATA_DIR

logger = setup_logger(__name__)

@dataclass
class AnalyticsData:
    """Analytics data container"""
    timestamp: datetime
    total_views: int = 0
    successful_views: int = 0
    failed_views: int = 0
    success_rate: float = 0.0
    active_tasks: int = 0
    active_accounts: int = 0
    active_proxies: int = 0
    requests_per_minute: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0

class AnalyticsService:
    """Advanced analytics service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.running = False
        self.analytics_data: List[AnalyticsData] = []
        self.reports_dir = DATA_DIR / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start analytics service"""
        self.running = True
        logger.info("Analytics service started")
        
        # Load historical data
        await self.load_historical_data()
        
        # Start background tasks
        asyncio.create_task(self.collect_metrics())
        asyncio.create_task(self.generate_reports())
        
    async def stop(self):
        """Stop analytics service"""
        self.running = False
        logger.info("Analytics service stopped")
        
    async def collect_metrics(self):
        """Collect metrics periodically"""
        while self.running:
            try:
                metrics = await self.gather_metrics()
                self.analytics_data.append(metrics)
                
                # Keep only last 1000 records
                if len(self.analytics_data) > 1000:
                    self.analytics_data = self.analytics_data[-1000:]
                
                # Save to file every 5 minutes
                if len(self.analytics_data) % 60 == 0:
                    await self.save_to_file()
                    
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
            
            await asyncio.sleep(5)  # Collect every 5 seconds
    
    async def gather_metrics(self) -> AnalyticsData:
        """Gather all metrics"""
        # Get database metrics
        total_tests = self.db.query(Test).count()
        successful_tests = self.db.query(Test).filter(Test.status == 'completed').count()
        
        # Calculate views
        total_views = sum(test.view_count for test in self.db.query(Test).all())
        successful_views = sum(test.views_sent for test in self.db.query(Test).all())
        failed_views = total_views - successful_views
        
        # Calculate success rate
        success_rate = (successful_views / total_views * 100) if total_views > 0 else 0
        
        # Get active counts
        active_accounts = self.db.query(TikTokAccount).filter(
            TikTokAccount.status == 'active'
        ).count()
        
        active_proxies = self.db.query(Proxy).filter(
            Proxy.is_active == True
        ).count()
        
        # Get system metrics (simplified)
        import psutil
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().percent
        
        return AnalyticsData(
            timestamp=datetime.now(),
            total_views=total_views,
            successful_views=successful_views,
            failed_views=failed_views,
            success_rate=success_rate,
            active_tasks=self.db.query(Test).filter(
                Test.status.in_(['pending', 'processing'])
            ).count(),
            active_accounts=active_accounts,
            active_proxies=active_proxies,
            requests_per_minute=await self.calculate_rpm(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
    
    async def calculate_rpm(self) -> float:
        """Calculate requests per minute"""
        try:
            # Get tests from last minute
            one_minute_ago = datetime.now() - timedelta(minutes=1)
            recent_tests = self.db.query(Test).filter(
                Test.created_at >= one_minute_ago
            ).all()
            
            if not recent_tests:
                return 0.0
            
            total_requests = sum(test.view_count for test in recent_tests)
            return total_requests / 1.0  # Per minute
            
        except Exception as e:
            logger.error(f"Error calculating RPM: {e}")
            return 0.0
    
    async def generate_reports(self):
        """Generate periodic reports"""
        while self.running:
            try:
                # Generate daily report at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute < 5:
                    await self.generate_daily_report()
                
                # Generate hourly report
                if now.minute == 0:
                    await self.generate_hourly_report()
                    
            except Exception as e:
                logger.error(f"Error generating reports: {e}")
            
            await asyncio.sleep(60)  # Check every minute
    
    async def generate_daily_report(self):
        """Generate daily analytics report"""
        try:
            logger.info("Generating daily analytics report...")
            
            # Get data for last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            
            # Query data
            daily_tests = self.db.query(Test).filter(
                Test.created_at >= yesterday
            ).all()
            
            # Calculate metrics
            total_tests = len(daily_tests)
            total_views = sum(test.view_count for test in daily_tests)
            successful_views = sum(test.views_sent for test in daily_tests)
            failed_views = total_views - successful_views
            success_rate = (successful_views / total_views * 100) if total_views > 0 else 0
            
            # Create report
            report = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "period": "daily",
                "total_tests": total_tests,
                "total_views": total_views,
                "successful_views": successful_views,
                "failed_views": failed_views,
                "success_rate": success_rate,
                "peak_rpm": max([data.requests_per_minute for data in self.analytics_data[-1440:]] or [0]),
                "average_success_rate": self.calculate_average_success_rate(),
                "top_performing_accounts": await self.get_top_accounts(),
                "top_performing_proxies": await self.get_top_proxies(),
                "system_health": {
                    "avg_cpu_usage": self.calculate_average_cpu_usage(),
                    "avg_memory_usage": self.calculate_average_memory_usage(),
                    "total_errors": self.db.query(SystemLog).filter(
                        SystemLog.level == 'error',
                        SystemLog.created_at >= yesterday
                    ).count()
                }
            }
            
            # Save report
            report_file = self.reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(report, indent=2, default=str))
            
            logger.info(f"Daily report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    async def generate_hourly_report(self):
        """Generate hourly analytics report"""
        try:
            # Get data for last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            hourly_tests = self.db.query(Test).filter(
                Test.created_at >= one_hour_ago
            ).all()
            
            if not hourly_tests:
                return
            
            # Calculate metrics
            total_views = sum(test.view_count for test in hourly_tests)
            successful_views = sum(test.views_sent for test in hourly_tests)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "period": "hourly",
                "total_tests": len(hourly_tests),
                "total_views": total_views,
                "successful_views": successful_views,
                "success_rate": (successful_views / total_views * 100) if total_views > 0 else 0
            }
            
            # Save report
            report_file = self.reports_dir / f"hourly_{datetime.now().strftime('%Y%m%d_%H')}.json"
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(report, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Error generating hourly report: {e}")
    
    async def get_top_accounts(self, limit: int = 5) -> List[Dict]:
        """Get top performing accounts"""
        try:
            accounts = self.db.query(TikTokAccount).filter(
                TikTokAccount.view_count > 0
            ).order_by(TikTokAccount.success_rate.desc()).limit(limit).all()
            
            return [
                {
                    "username": acc.username,
                    "view_count": acc.view_count,
                    "success_rate": acc.success_rate,
                    "status": acc.status
                }
                for acc in accounts
            ]
        except Exception as e:
            logger.error(f"Error getting top accounts: {e}")
            return []
    
    async def get_top_proxies(self, limit: int = 5) -> List[Dict]:
        """Get top performing proxies"""
        try:
            proxies = self.db.query(Proxy).filter(
                Proxy.success_rate > 0
            ).order_by(Proxy.success_rate.desc()).limit(limit).all()
            
            return [
                {
                    "proxy_url": proxy.proxy_url[:50] + "..." if len(proxy.proxy_url) > 50 else proxy.proxy_url,
                    "proxy_type": proxy.proxy_type,
                    "success_rate": proxy.success_rate,
                    "speed": proxy.speed
                }
                for proxy in proxies
            ]
        except Exception as e:
            logger.error(f"Error getting top proxies: {e}")
            return []
    
    def calculate_average_success_rate(self) -> float:
        """Calculate average success rate from analytics data"""
        if not self.analytics_data:
            return 0.0
        
        rates = [data.success_rate for data in self.analytics_data if data.success_rate > 0]
        return sum(rates) / len(rates) if rates else 0.0
    
    def calculate_average_cpu_usage(self) -> float:
        """Calculate average CPU usage"""
        if not self.analytics_data:
            return 0.0
        
        usages = [data.cpu_usage for data in self.analytics_data]
        return sum(usages) / len(usages)
    
    def calculate_average_memory_usage(self) -> float:
        """Calculate average memory usage"""
        if not self.analytics_data:
            return 0.0
        
        usages = [data.memory_usage for data in self.analytics_data]
        return sum(usages) / len(usages)
    
    async def save_to_file(self):
        """Save analytics data to file"""
        try:
            data_file = self.reports_dir / "analytics_data.json"
            data = [asdict(d) for d in self.analytics_data]
            
            async with aiofiles.open(data_file, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
                
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")
    
    async def load_historical_data(self):
        """Load historical analytics data"""
        try:
            data_file = self.reports_dir / "analytics_data.json"
            if data_file.exists():
                async with aiofiles.open(data_file, 'r') as f:
                    data = json.loads(await f.read())
                    
                self.analytics_data = [
                    AnalyticsData(
                        timestamp=datetime.fromisoformat(d['timestamp']),
                        **{k: v for k, v in d.items() if k != 'timestamp'}
                    )
                    for d in data
                ]
                logger.info(f"Loaded {len(self.analytics_data)} historical analytics records")
                
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def get_summary(self) -> Dict:
        """Get analytics summary"""
        if not self.analytics_data:
            return {}
        
        latest = self.analytics_data[-1]
        
        return {
            "current_success_rate": latest.success_rate,
            "current_rpm": latest.requests_per_minute,
            "total_views_today": self.get_views_today(),
            "average_success_rate": self.calculate_average_success_rate(),
            "system_health": {
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage
            }
        }
    
    def get_views_today(self) -> int:
        """Get total views sent today"""
        today = datetime.now().date()
        
        today_tests = self.db.query(Test).filter(
            Test.created_at >= datetime.combine(today, datetime.min.time())
        ).all()
        
        return sum(test.view_count for test in today_tests)