"""
Report Generation Service
Advanced reporting and analytics
"""

import asyncio
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

import aiofiles
from sqlalchemy.orm import Session

from utils.logger import setup_logger
from utils.formatter import format_number, format_bytes, format_percentage
from database.crud import (
    get_test_statistics, get_account_statistics, 
    get_proxy_statistics, get_recent_tests,
    get_active_accounts, get_active_proxies
)
from database.models import SessionLocal
from config import DATA_DIR, Colors

logger = setup_logger(__name__)

class ReportGenerator:
    """Advanced report generator"""
    
    def __init__(self):
        self.reports_dir = DATA_DIR / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily report"""
        if date is None:
            date = datetime.now()
        
        logger.info(f"Generating daily report for {date.date()}")
        
        db = SessionLocal()
        try:
            # Get statistics
            test_stats = get_test_statistics(db)
            account_stats = get_account_statistics(db)
            proxy_stats = get_proxy_statistics(db)
            
            # Get recent tests
            recent_tests = get_recent_tests(db, hours=24, limit=10)
            
            # Get system information
            system_info = await self._get_system_info()
            
            # Compile report
            report = {
                "report_type": "daily",
                "date": date.date().isoformat(),
                "generated_at": datetime.now().isoformat(),
                "test_statistics": test_stats,
                "account_statistics": account_stats,
                "proxy_statistics": proxy_stats,
                "recent_tests": [
                    {
                        "id": test.id,
                        "task_id": test.task_id,
                        "video_url": test.video_url[:100] + "..." if len(test.video_url) > 100 else test.video_url,
                        "view_count": test.view_count,
                        "views_sent": test.views_sent,
                        "status": test.status,
                        "created_at": test.created_at.isoformat()
                    }
                    for test in recent_tests
                ],
                "system_info": system_info,
                "summary": self._generate_summary(test_stats, account_stats, proxy_stats)
            }
            
            # Save report
            report_file = self.reports_dir / f"daily_report_{date.date().isoformat()}.json"
            await self._save_json_report(report_file, report)
            
            # Generate text summary
            text_report = await self._generate_text_report(report)
            text_file = self.reports_dir / f"daily_summary_{date.date().isoformat()}.txt"
            await self._save_text_report(text_file, text_report)
            
            logger.info(f"Daily report generated: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return {}
        finally:
            db.close()
    
    async def generate_weekly_report(self, start_date: datetime = None) -> Dict[str, Any]:
        """Generate weekly report"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        
        end_date = start_date + timedelta(days=6)
        
        logger.info(f"Generating weekly report from {start_date.date()} to {end_date.date()}")
        
        # For weekly report, we would aggregate daily reports
        # This is a simplified version
        db = SessionLocal()
        try:
            # Get weekly statistics
            # In a real implementation, you would query for the entire week
            
            report = {
                "report_type": "weekly",
                "period": {
                    "start": start_date.date().isoformat(),
                    "end": end_date.date().isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "summary": "Weekly report summary (simplified)",
                "note": "Full weekly report would include aggregated statistics"
            }
            
            # Save report
            report_file = self.reports_dir / f"weekly_report_{start_date.date().isoformat()}_to_{end_date.date().isoformat()}.json"
            await self._save_json_report(report_file, report)
            
            logger.info(f"Weekly report generated: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {}
        finally:
            db.close()
    
    async def generate_custom_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        report_type: str = "custom"
    ) -> Dict[str, Any]:
        """Generate custom date range report"""
        logger.info(f"Generating custom report from {start_date.date()} to {end_date.date()}")
        
        db = SessionLocal()
        try:
            # This would implement actual date range queries
            # For now, return a template
            
            report = {
                "report_type": report_type,
                "period": {
                    "start": start_date.date().isoformat(),
                    "end": end_date.date().isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "data_available": False,
                "note": "Custom report generation would query data between specified dates"
            }
            
            report_file = self.reports_dir / f"custom_report_{start_date.date().isoformat()}_to_{end_date.date().isoformat()}.json"
            await self._save_json_report(report_file, report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating custom report: {e}")
            return {}
        finally:
            db.close()
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate performance analysis report"""
        logger.info("Generating performance report")
        
        db = SessionLocal()
        try:
            # Get performance metrics
            test_stats = get_test_statistics(db)
            account_stats = get_account_statistics(db)
            proxy_stats = get_proxy_statistics(db)
            
            # Calculate performance metrics
            performance = {
                "overall_success_rate": test_stats.get("success_rate", 0),
                "views_per_hour": await self._calculate_views_per_hour(db),
                "account_efficiency": account_stats.get("average_success_rate", 0),
                "proxy_efficiency": proxy_stats.get("average_success_rate", 0),
                "system_uptime": await self._get_system_uptime(),
                "recommendations": await self._generate_recommendations(
                    test_stats, account_stats, proxy_stats
                )
            }
            
            report = {
                "report_type": "performance",
                "generated_at": datetime.now().isoformat(),
                "performance_metrics": performance,
                "test_statistics": test_stats,
                "account_statistics": account_stats,
                "proxy_statistics": proxy_stats
            }
            
            report_file = self.reports_dir / f"performance_report_{datetime.now().date().isoformat()}.json"
            await self._save_json_report(report_file, report)
            
            logger.info(f"Performance report generated: {report_file}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {}
        finally:
            db.close()
    
    async def export_report_to_csv(self, report_data: Dict[str, Any], output_file: Path) -> bool:
        """Export report data to CSV"""
        try:
            # Flatten the report data for CSV
            flat_data = self._flatten_report_data(report_data)
            
            # Write to CSV
            async with aiofiles.open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                if flat_data:
                    writer.writerow(flat_data[0].keys())
                    
                    # Write rows
                    for row in flat_data:
                        writer.writerow(row.values())
            
            logger.info(f"Report exported to CSV: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report to CSV: {e}")
            return False
    
    # Helper methods
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            import psutil
            import platform
            
            system_info = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "total_memory": psutil.virtual_memory().total,
                "total_memory_human": format_bytes(psutil.virtual_memory().total),
                "disk_usage": psutil.disk_usage('/').percent,
                "system_uptime": time.time() - psutil.boot_time(),
                "process_uptime": time.time() - psutil.Process().create_time()
            }
            
            return system_info
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def _generate_summary(
        self, 
        test_stats: Dict[str, Any], 
        account_stats: Dict[str, Any], 
        proxy_stats: Dict[str, Any]
    ) -> str:
        """Generate report summary"""
        summary_parts = []
        
        if test_stats.get("total_views", 0) > 0:
            summary_parts.append(
                f"Sent {format_number(test_stats['total_views'])} views "
                f"with {test_stats.get('success_rate', 0):.1f}% success rate"
            )
        
        if account_stats.get("active_accounts", 0) > 0:
            summary_parts.append(
                f"{account_stats['active_accounts']} active accounts "
                f"(avg success: {account_stats.get('average_success_rate', 0):.1f}%)"
            )
        
        if proxy_stats.get("active_proxies", 0) > 0:
            summary_parts.append(
                f"{proxy_stats['active_proxies']} active proxies "
                f"(avg success: {proxy_stats.get('average_success_rate', 0):.1f}%)"
            )
        
        return " | ".join(summary_parts) if summary_parts else "No activity"
    
    async def _generate_text_report(self, report_data: Dict[str, Any]) -> str:
        """Generate human-readable text report"""
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append(f"VT VIEW TESTER - {report_data['report_type'].upper()} REPORT")
        lines.append(f"Date: {report_data.get('date', 'N/A')}")
        lines.append(f"Generated: {report_data.get('generated_at', 'N/A')}")
        lines.append("=" * 60)
        lines.append("")
        
        # Test Statistics
        if 'test_statistics' in report_data:
            test_stats = report_data['test_statistics']
            lines.append("📊 TEST STATISTICS")
            lines.append("-" * 40)
            lines.append(f"Total Tests: {format_number(test_stats.get('total_tests', 0))}")
            lines.append(f"Total Views: {format_number(test_stats.get('total_views', 0))}")
            lines.append(f"Successful Views: {format_number(test_stats.get('total_sent', 0))}")
            lines.append(f"Failed Views: {format_number(test_stats.get('total_failed', 0))}")
            lines.append(f"Success Rate: {format_percentage(test_stats.get('success_rate', 0))}")
            lines.append(f"Today's Tests: {format_number(test_stats.get('today_tests', 0))}")
            lines.append(f"Today's Views: {format_number(test_stats.get('today_views', 0))}")
            lines.append("")
        
        # Account Statistics
        if 'account_statistics' in report_data:
            acc_stats = report_data['account_statistics']
            lines.append("👤 ACCOUNT STATISTICS")
            lines.append("-" * 40)
            lines.append(f"Total Accounts: {format_number(acc_stats.get('total_accounts', 0))}")
            lines.append(f"Active Accounts: {format_number(acc_stats.get('active_accounts', 0))}")
            lines.append(f"Banned Accounts: {format_number(acc_stats.get('banned_accounts', 0))}")
            lines.append(f"Total Views: {format_number(acc_stats.get('total_views', 0))}")
            lines.append(f"Avg Success Rate: {format_percentage(acc_stats.get('average_success_rate', 0))}")
            lines.append("")
        
        # Proxy Statistics
        if 'proxy_statistics' in report_data:
            proxy_stats = report_data['proxy_statistics']
            lines.append("🔗 PROXY STATISTICS")
            lines.append("-" * 40)
            lines.append(f"Total Proxies: {format_number(proxy_stats.get('total_proxies', 0))}")
            lines.append(f"Active Proxies: {format_number(proxy_stats.get('active_proxies', 0))}")
            lines.append(f"Avg Speed: {proxy_stats.get('average_speed', 0):.0f}ms")
            lines.append(f"Avg Success Rate: {format_percentage(proxy_stats.get('average_success_rate', 0))}")
            lines.append("")
        
        # Summary
        if 'summary' in report_data:
            lines.append("📈 SUMMARY")
            lines.append("-" * 40)
            lines.append(report_data['summary'])
            lines.append("")
        
        # Footer
        lines.append("=" * 60)
        lines.append(f"Report generated by VT View Tester v{__import__('config').VERSION}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    async def _save_json_report(self, file_path: Path, data: Dict[str, Any]):
        """Save report as JSON"""
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, default=str))
    
    async def _save_text_report(self, file_path: Path, content: str):
        """Save report as text"""
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
    
    def _flatten_report_data(self, data: Dict[str, Any], prefix: str = "") -> List[Dict[str, Any]]:
        """Flatten nested report data for CSV export"""
        flat_rows = []
        
        def flatten(item, parent_key=""):
            if isinstance(item, dict):
                for k, v in item.items():
                    new_key = f"{parent_key}.{k}" if parent_key else k
                    flatten(v, new_key)
            elif isinstance(item, list):
                for i, elem in enumerate(item):
                    new_key = f"{parent_key}[{i}]" if parent_key else f"[{i}]"
                    flatten(elem, new_key)
            else:
                flat_rows.append({parent_key: item})
        
        flatten(data)
        return flat_rows
    
    async def _calculate_views_per_hour(self, db: Session) -> float:
        """Calculate views per hour"""
        try:
            # Get views from last 24 hours
            yesterday = datetime.now() - timedelta(hours=24)
            
            from database.models import Test
            from sqlalchemy import func
            
            total_views = db.query(func.sum(Test.view_count))\
                .filter(Test.created_at >= yesterday)\
                .scalar() or 0
            
            return total_views / 24
            
        except Exception as e:
            logger.error(f"Error calculating views per hour: {e}")
            return 0.0
    
    async def _get_system_uptime(self) -> float:
        """Get system uptime in hours"""
        try:
            import psutil
            uptime_seconds = time.time() - psutil.boot_time()
            return uptime_seconds / 3600
        except Exception:
            return 0.0
    
    async def _generate_recommendations(
        self,
        test_stats: Dict[str, Any],
        account_stats: Dict[str, Any],
        proxy_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on statistics"""
        recommendations = []
        
        # Check success rate
        if test_stats.get("success_rate", 0) < 70:
            recommendations.append("Consider adding more proxies to improve success rate")
        
        # Check account count
        if account_stats.get("active_accounts", 0) < 10:
            recommendations.append("Add more active accounts for better rotation")
        
        # Check proxy count
        if proxy_stats.get("active_proxies", 0) < 20:
            recommendations.append("Increase proxy pool size for better IP rotation")
        
        # Check proxy success rate
        if proxy_stats.get("average_success_rate", 0) < 60:
            recommendations.append("Test and remove low-performing proxies")
        
        if not recommendations:
            recommendations.append("System is performing well. Keep up the good work!")
        
        return recommendations
    
    async def list_reports(self, report_type: str = None) -> List[Dict[str, Any]]:
        """List available reports"""
        reports = []
        
        try:
            for report_file in self.reports_dir.glob("*.json"):
                try:
                    async with aiofiles.open(report_file, 'r') as f:
                        content = await f.read()
                        report_data = json.loads(content)
                        
                        if report_type and report_data.get("report_type") != report_type:
                            continue
                        
                        reports.append({
                            "file": report_file.name,
                            "type": report_data.get("report_type", "unknown"),
                            "date": report_data.get("date", report_data.get("generated_at", "")),
                            "size": report_file.stat().st_size
                        })
                        
                except Exception as e:
                    logger.error(f"Error reading report {report_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error listing reports: {e}")
        
        # Sort by date (newest first)
        reports.sort(key=lambda x: x["date"], reverse=True)
        
        return reports