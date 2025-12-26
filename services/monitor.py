"""
System Monitor Service
Real-time system health monitoring
"""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, List, Optional

from utils.logger import setup_logger
from config import (
    CPU_LIMIT, MEMORY_LIMIT, DISK_LIMIT,
    Colors
)

logger = setup_logger(__name__)

class SystemMonitor:
    """System health monitor"""
    
    def __init__(self):
        self.running = False
        self.metrics_history: List[Dict] = []
        self.alerts: List[Dict] = []
        self.max_history = 1000
        
    async def start(self):
        """Start monitoring service"""
        self.running = True
        logger.info("System monitor started")
        
        # Start monitoring loop
        asyncio.create_task(self.monitor_loop())
        
    async def stop(self):
        """Stop monitoring service"""
        self.running = False
        logger.info("System monitor stopped")
        
    async def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep history limited
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                # Check for alerts
                await self.check_alerts(metrics)
                
                # Log periodic summary
                if len(self.metrics_history) % 12 == 0:  # Every minute
                    await self.log_summary()
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(5)  # Monitor every 5 seconds
    
    async def collect_metrics(self) -> Dict:
        """Collect system metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        # Process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent(interval=0.1)
        
        return {
            "timestamp": timestamp.isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "percent": swap.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process_cpu,
                "threads": process.num_threads(),
                "open_files": len(process.open_files())
            }
        }
    
    async def check_alerts(self, metrics: Dict):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if metrics["cpu"]["percent"] > CPU_LIMIT:
            alerts.append({
                "level": "warning",
                "metric": "cpu",
                "value": metrics["cpu"]["percent"],
                "threshold": CPU_LIMIT,
                "message": f"CPU usage high: {metrics['cpu']['percent']}%"
            })
        
        # Memory alert
        if metrics["memory"]["percent"] > MEMORY_LIMIT:
            alerts.append({
                "level": "warning",
                "metric": "memory",
                "value": metrics["memory"]["percent"],
                "threshold": MEMORY_LIMIT,
                "message": f"Memory usage high: {metrics['memory']['percent']}%"
            })
        
        # Disk alert
        if metrics["disk"]["percent"] > DISK_LIMIT:
            alerts.append({
                "level": "warning",
                "metric": "disk",
                "value": metrics["disk"]["percent"],
                "threshold": DISK_LIMIT,
                "message": f"Disk usage high: {metrics['disk']['percent']}%"
            })
        
        # Process memory alert (if > 1GB)
        process_memory_gb = metrics["process"]["memory_rss"] / (1024**3)
        if process_memory_gb > 1.0:
            alerts.append({
                "level": "warning",
                "metric": "process_memory",
                "value": process_memory_gb,
                "threshold": 1.0,
                "message": f"Process memory high: {process_memory_gb:.2f}GB"
            })
        
        # Add alerts to history
        for alert in alerts:
            self.alerts.append({
                **alert,
                "timestamp": metrics["timestamp"]
            })
            
            # Log critical alerts
            if alert["level"] == "critical":
                logger.warning(f"ALERT: {alert['message']}")
    
    async def log_summary(self):
        """Log periodic summary"""
        if not self.metrics_history:
            return
        
        latest = self.metrics_history[-1]
        
        summary = (
            f"📊 System Summary - "
            f"CPU: {latest['cpu']['percent']:.1f}% | "
            f"RAM: {latest['memory']['percent']:.1f}% | "
            f"Disk: {latest['disk']['percent']:.1f}%"
        )
        
        logger.info(summary)
    
    def get_current_metrics(self) -> Dict:
        """Get current metrics"""
        if not self.metrics_history:
            return {}
        
        return self.metrics_history[-1]
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict]:
        """Get metrics history"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-limit:] if self.alerts else []
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "No metrics available"}
        
        latest = self.metrics_history[-1]
        
        # Check health conditions
        issues = []
        
        if latest["cpu"]["percent"] > CPU_LIMIT:
            issues.append(f"CPU usage high ({latest['cpu']['percent']:.1f}%)")
        
        if latest["memory"]["percent"] > MEMORY_LIMIT:
            issues.append(f"Memory usage high ({latest['memory']['percent']:.1f}%)")
        
        if latest["disk"]["percent"] > DISK_LIMIT:
            issues.append(f"Disk usage high ({latest['disk']['percent']:.1f}%)")
        
        if issues:
            return {
                "status": "warning",
                "message": ", ".join(issues),
                "details": latest
            }
        else:
            return {
                "status": "healthy",
                "message": "All systems normal",
                "details": latest
            }
    
    def format_metrics_for_display(self) -> str:
        """Format metrics for terminal display"""
        if not self.metrics_history:
            return "No metrics available"
        
        latest = self.metrics_history[-1]
        
        # Color coding based on thresholds
        cpu_color = Colors.RED if latest["cpu"]["percent"] > CPU_LIMIT else Colors.GREEN
        mem_color = Colors.RED if latest["memory"]["percent"] > MEMORY_LIMIT else Colors.GREEN
        disk_color = Colors.RED if latest["disk"]["percent"] > DISK_LIMIT else Colors.GREEN
        
        return f"""
{Colors.CYAN}{'='*60}{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}📊 SYSTEM MONITOR{Colors.RESET}
{Colors.CYAN}{'='*60}{Colors.RESET}

{Colors.BOLD}CPU Usage:{Colors.RESET} {cpu_color}{latest['cpu']['percent']:.1f}%{Colors.RESET}
{Colors.BOLD}Memory Usage:{Colors.RESET} {mem_color}{latest['memory']['percent']:.1f}%{Colors.RESET}
{Colors.BOLD}Disk Usage:{Colors.RESET} {disk_color}{latest['disk']['percent']:.1f}%{Colors.RESET}

{Colors.BOLD}Process Memory:{Colors.RESET} {latest['process']['memory_rss'] / (1024**2):.1f} MB
{Colors.BOLD}Process CPU:{Colors.RESET} {latest['process']['cpu_percent']:.1f}%
{Colors.BOLD}Threads:{Colors.RESET} {latest['process']['threads']}

{Colors.BOLD}Network:{Colors.RESET}
  Sent: {latest['network']['bytes_sent'] / (1024**2):.1f} MB
  Received: {latest['network']['bytes_recv'] / (1024**2):.1f} MB

{Colors.BOLD}Recent Alerts:{Colors.RESET} {len(self.alerts[-10:])}
{Colors.CYAN}{'='*60}{Colors.RESET}
"""