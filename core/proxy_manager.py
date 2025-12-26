"""
Advanced Proxy Manager
Professional proxy management with validation and rotation
"""

import asyncio
import aiohttp
import random
import socket
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from utils.logger import setup_logger
from utils.file_handler import FileHandler
from database.crud import (
    create_proxy, get_proxy, update_proxy, 
    get_active_proxies, update_proxy_success_rate,
    bulk_create_proxies
)
from database.models import SessionLocal
from config import PROXIES_DIR, Colors

logger = setup_logger(__name__)

@dataclass
class ProxyInfo:
    """Proxy information container"""
    url: str
    proxy_type: str  # http, https, socks4, socks5
    country: Optional[str] = None
    speed: Optional[float] = None  # in milliseconds
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = None
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "proxy_type": self.proxy_type,
            "country": self.country,
            "speed": self.speed,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "last_tested": self.last_tested.isoformat() if self.last_tested else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ProxyValidator:
    """Proxy validation and testing"""
    
    def __init__(self):
        self.test_urls = [
            "http://www.google.com",
            "http://www.tiktok.com",
            "http://httpbin.org/ip"
        ]
        self.timeout = 10
        self.executor = ThreadPoolExecutor(max_workers=20)
    
    async def validate_proxy(self, proxy_info: ProxyInfo) -> Tuple[bool, float]:
        """Validate proxy connectivity and speed"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout
            ) as session:
                
                # Test with a simple request
                test_url = random.choice(self.test_urls)
                
                try:
                    async with session.get(
                        test_url,
                        proxy=proxy_info.url,
                        allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            end_time = asyncio.get_event_loop().time()
                            speed = (end_time - start_time) * 1000  # Convert to ms
                            
                            # Get response content for IP verification
                            content = await response.text()
                            
                            return True, speed
                        
                except aiohttp.ClientProxyConnectionError:
                    return False, 0
                except aiohttp.ClientConnectorError:
                    return False, 0
                except asyncio.TimeoutError:
                    return False, 0
                except Exception:
                    return False, 0
                
        except Exception as e:
            logger.debug(f"Proxy validation error: {e}")
            return False, 0
    
    async def batch_validate(self, proxies: List[ProxyInfo]) -> List[Tuple[ProxyInfo, bool, float]]:
        """Validate multiple proxies in parallel"""
        tasks = []
        for proxy in proxies:
            task = self.validate_proxy(proxy)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        validated = []
        for i, result in enumerate(results):
            if isinstance(result, tuple) and len(result) == 2:
                proxy = proxies[i]
                success, speed = result
                validated.append((proxy, success, speed))
            else:
                validated.append((proxies[i], False, 0))
        
        return validated
    
    def get_proxy_country(self, ip_address: str) -> Optional[str]:
        """Get country from IP address (simplified)"""
        # In a real implementation, you would use a GeoIP database
        # This is a simplified version
        try:
            # This would typically use a GeoIP service
            # For now, return None or simulate
            return "Unknown"
        except Exception:
            return None

class ProxyManager:
    """Advanced proxy manager with validation and rotation"""
    
    def __init__(self):
        self.file_handler = FileHandler(PROXIES_DIR)
        self.proxies_file = PROXIES_DIR / "proxies.json"
        self.validator = ProxyValidator()
        self.proxies_cache: List[ProxyInfo] = []
        self.rotation_index = 0
        self.active_proxies: List[ProxyInfo] = []
        
    async def initialize(self):
        """Initialize proxy manager"""
        logger.info("Initializing Proxy Manager...")
        
        # Load proxies from file
        await self.load_proxies_from_file()
        
        # Sync with database
        await self.sync_with_database()
        
        # Update active proxies list
        self.active_proxies = [p for p in self.proxies_cache if p.is_active]
        
        logger.info(f"Proxy Manager initialized with {len(self.proxies_cache)} proxies")
    
    async def load_proxies_from_file(self):
        """Load proxies from file"""
        try:
            if await self.file_handler.file_exists(self.proxies_file):
                proxies_data = await self.file_handler.read_json(self.proxies_file)
                
                self.proxies_cache = []
                for proxy_data in proxies_data:
                    proxy = ProxyInfo(
                        url=proxy_data["url"],
                        proxy_type=proxy_data.get("proxy_type", "http"),
                        country=proxy_data.get("country"),
                        speed=proxy_data.get("speed"),
                        success_rate=proxy_data.get("success_rate", 0.0),
                        last_used=datetime.fromisoformat(proxy_data["last_used"]) if proxy_data.get("last_used") else None,
                        last_tested=datetime.fromisoformat(proxy_data["last_tested"]) if proxy_data.get("last_tested") else None,
                        is_active=proxy_data.get("is_active", True),
                        created_at=datetime.fromisoformat(proxy_data["created_at"]) if proxy_data.get("created_at") else datetime.now()
                    )
                    self.proxies_cache.append(proxy)
                
                logger.info(f"Loaded {len(self.proxies_cache)} proxies from file")
            else:
                logger.info("No proxies file found, starting fresh")
                self.proxies_cache = []
                
        except Exception as e:
            logger.error(f"Error loading proxies from file: {e}")
            self.proxies_cache = []
    
    async def save_proxies_to_file(self):
        """Save proxies to file"""
        try:
            proxies_data = [proxy.to_dict() for proxy in self.proxies_cache]
            await self.file_handler.write_json(self.proxies_file, proxies_data)
            logger.info(f"Saved {len(self.proxies_cache)} proxies to file")
            
        except Exception as e:
            logger.error(f"Error saving proxies to file: {e}")
    
    async def sync_with_database(self):
        """Sync proxies with database"""
        try:
            db = SessionLocal()
            
            # Add proxies from cache to database
            for proxy in self.proxies_cache:
                # Check if proxy exists in database
                existing = None
                try:
                    # Simple check by URL
                    # In real implementation, you'd have a proper check
                    pass
                except:
                    pass
                
                if not existing:
                    create_proxy(
                        db,
                        proxy_url=proxy.url,
                        proxy_type=proxy.proxy_type,
                        country=proxy.country,
                        speed=proxy.speed
                    )
            
            db.commit()
            logger.info("Synced proxies with database")
            
        except Exception as e:
            logger.error(f"Error syncing with database: {e}")
        finally:
            db.close()
    
    async def add_proxy(
        self,
        proxy_url: str,
        proxy_type: str = "http",
        country: str = None,
        speed: float = None
    ) -> bool:
        """Add a new proxy"""
        try:
            # Parse and validate URL
            parsed = urlparse(proxy_url)
            if not parsed.scheme or not parsed.netloc:
                logger.error(f"Invalid proxy URL: {proxy_url}")
                return False
            
            # Check if proxy already exists
            existing = await self.get_proxy(proxy_url)
            if existing:
                logger.warning(f"Proxy {proxy_url} already exists")
                return False
            
            # Create new proxy
            proxy = ProxyInfo(
                url=proxy_url,
                proxy_type=proxy_type,
                country=country,
                speed=speed,
                created_at=datetime.now()
            )
            
            # Add to cache
            self.proxies_cache.append(proxy)
            
            # Save to file
            await self.save_proxies_to_file()
            
            # Add to database
            db = SessionLocal()
            try:
                create_proxy(
                    db,
                    proxy_url=proxy_url,
                    proxy_type=proxy_type,
                    country=country,
                    speed=speed
                )
                db.commit()
            except Exception as e:
                logger.error(f"Error adding proxy to database: {e}")
                db.rollback()
            finally:
                db.close()
            
            logger.info(f"Added proxy: {proxy_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding proxy {proxy_url}: {e}")
            return False
    
    async def add_proxies_bulk(self, proxies_list: List[str]) -> int:
        """Add multiple proxies at once"""
        added_count = 0
        
        for proxy_url in proxies_list:
            # Try to detect proxy type
            proxy_type = "http"
            if proxy_url.startswith("socks4://"):
                proxy_type = "socks4"
            elif proxy_url.startswith("socks5://"):
                proxy_type = "socks5"
            elif proxy_url.startswith("https://"):
                proxy_type = "https"
            
            success = await self.add_proxy(proxy_url, proxy_type)
            
            if success:
                added_count += 1
        
        logger.info(f"Added {added_count} proxies in bulk")
        return added_count
    
    async def get_proxy(self, proxy_url: str) -> Optional[ProxyInfo]:
        """Get proxy by URL"""
        for proxy in self.proxies_cache:
            if proxy.url == proxy_url:
                return proxy
        return None
    
    async def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get next proxy for rotation"""
        if not self.active_proxies:
            # Refresh active proxies list
            self.active_proxies = [p for p in self.proxies_cache if p.is_active]
            
            if not self.active_proxies:
                logger.warning("No active proxies available")
                return None
        
        # Sort by success rate and speed
        sorted_proxies = sorted(
            self.active_proxies,
            key=lambda p: (p.success_rate, -p.speed if p.speed else 0),
            reverse=True
        )
        
        # Take top 10% for random selection (load balancing)
        top_count = max(1, len(sorted_proxies) // 10)
        top_proxies = sorted_proxies[:top_count]
        
        # Random selection from top performers
        proxy = random.choice(top_proxies)
        
        # Update last used
        proxy.last_used = datetime.now()
        
        # Save changes
        await self.save_proxies_to_file()
        
        return proxy
    
    async def validate_proxy(self, proxy_url: str) -> Tuple[bool, float]:
        """Validate specific proxy"""
        proxy = await self.get_proxy(proxy_url)
        if not proxy:
            return False, 0
        
        success, speed = await self.validator.validate_proxy(proxy)
        
        # Update proxy info
        proxy.last_tested = datetime.now()
        proxy.speed = speed
        proxy.success_rate = (proxy.success_rate * 9 + (1 if success else 0)) / 10
        proxy.is_active = success
        
        # Update in database
        db = SessionLocal()
        try:
            update_proxy_success_rate(db, self._get_proxy_id(proxy_url), success)
            db.commit()
        except Exception as e:
            logger.error(f"Error updating proxy in database: {e}")
            db.rollback()
        finally:
            db.close()
        
        await self.save_proxies_to_file()
        
        return success, speed
    
    async def validate_all_proxies(self, batch_size: int = 20) -> Dict[str, Any]:
        """Validate all proxies in batches"""
        logger.info(f"Starting validation of {len(self.proxies_cache)} proxies...")
        
        results = {
            "total": len(self.proxies_cache),
            "valid": 0,
            "invalid": 0,
            "avg_speed": 0,
            "details": []
        }
        
        # Process in batches
        for i in range(0, len(self.proxies_cache), batch_size):
            batch = self.proxies_cache[i:i + batch_size]
            validated = await self.validator.batch_validate(batch)
            
            for proxy, success, speed in validated:
                proxy.last_tested = datetime.now()
                proxy.speed = speed if success else None
                proxy.success_rate = (proxy.success_rate * 9 + (1 if success else 0)) / 10
                proxy.is_active = success
                
                results["details"].append({
                    "url": proxy.url,
                    "success": success,
                    "speed": speed,
                    "success_rate": proxy.success_rate
                })
                
                if success:
                    results["valid"] += 1
                    results["avg_speed"] += speed
                else:
                    results["invalid"] += 1
            
            logger.info(f"Validated batch {i//batch_size + 1}/{(len(self.proxies_cache) + batch_size - 1)//batch_size}")
        
        # Calculate average speed
        if results["valid"] > 0:
            results["avg_speed"] /= results["valid"]
        
        # Save changes
        await self.save_proxies_to_file()
        
        # Update active proxies list
        self.active_proxies = [p for p in self.proxies_cache if p.is_active]
        
        logger.info(f"Validation complete: {results['valid']} valid, {results['invalid']} invalid")
        return results
    
    async def update_proxy_status(self, proxy_url: str, is_active: bool) -> bool:
        """Update proxy active status"""
        try:
            proxy = await self.get_proxy(proxy_url)
            if not proxy:
                return False
            
            proxy.is_active = is_active
            proxy.last_tested = datetime.now()
            
            # Update active proxies list
            if is_active and proxy not in self.active_proxies:
                self.active_proxies.append(proxy)
            elif not is_active and proxy in self.active_proxies:
                self.active_proxies.remove(proxy)
            
            # Update in database
            db = SessionLocal()
            try:
                proxy_id = self._get_proxy_id(proxy_url)
                if proxy_id:
                    update_proxy(db, proxy_id, is_active=is_active)
                    db.commit()
            except Exception as e:
                logger.error(f"Error updating proxy in database: {e}")
                db.rollback()
            finally:
                db.close()
            
            await self.save_proxies_to_file()
            logger.info(f"Updated proxy {proxy_url} status to {'active' if is_active else 'inactive'}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating proxy status: {e}")
            return False
    
    async def remove_proxy(self, proxy_url: str) -> bool:
        """Remove proxy"""
        try:
            proxy = await self.get_proxy(proxy_url)
            if not proxy:
                return False
            
            # Remove from cache
            self.proxies_cache = [p for p in self.proxies_cache if p.url != proxy_url]
            
            # Remove from active list
            if proxy in self.active_proxies:
                self.active_proxies.remove(proxy)
            
            # Save changes
            await self.save_proxies_to_file()
            
            logger.info(f"Removed proxy: {proxy_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing proxy {proxy_url}: {e}")
            return False
    
    async def clean_inactive_proxies(self, days_inactive: int = 7) -> int:
        """Remove proxies inactive for specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            
            inactive_proxies = [
                p for p in self.proxies_cache 
                if p.last_tested and p.last_tested < cutoff_date and not p.is_active
            ]
            
            for proxy in inactive_proxies:
                await self.remove_proxy(proxy.url)
            
            logger.info(f"Cleaned {len(inactive_proxies)} inactive proxies")
            return len(inactive_proxies)
            
        except Exception as e:
            logger.error(f"Error cleaning inactive proxies: {e}")
            return 0
    
    async def export_proxies(self, format: str = "json") -> str:
        """Export proxies to specified format"""
        try:
            if format == "json":
                data = [proxy.to_dict() for proxy in self.proxies_cache]
                return json.dumps(data, indent=2, default=str)
            
            elif format == "csv":
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "url", "type", "country", "speed_ms", 
                    "success_rate", "last_tested", "status"
                ])
                
                # Write data
                for proxy in self.proxies_cache:
                    writer.writerow([
                        proxy.url,
                        proxy.proxy_type,
                        proxy.country or "",
                        f"{proxy.speed:.0f}" if proxy.speed else "",
                        f"{proxy.success_rate:.2f}",
                        proxy.last_tested.isoformat() if proxy.last_tested else "",
                        "active" if proxy.is_active else "inactive"
                    ])
                
                return output.getvalue()
            
            elif format == "txt":
                lines = []
                for proxy in self.proxies_cache:
                    lines.append(proxy.url)
                
                return "\n".join(lines)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting proxies: {e}")
            return ""
    
    async def import_proxies(self, file_path: Path, format: str = "txt") -> int:
        """Import proxies from file"""
        try:
            if not await self.file_handler.file_exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 0
            
            content = await self.file_handler.read_file(file_path)
            
            proxies_list = []
            
            if format == "txt":
                # One proxy per line
                proxies_list = [line.strip() for line in content.splitlines() if line.strip()]
            
            elif format == "csv":
                import csv
                from io import StringIO
                
                reader = csv.reader(StringIO(content))
                next(reader, None)  # Skip header
                
                for row in reader:
                    if row and row[0].strip():
                        proxies_list.append(row[0].strip())
            
            elif format == "json":
                data = json.loads(content)
                for item in data:
                    if isinstance(item, dict) and "url" in item:
                        proxies_list.append(item["url"])
                    elif isinstance(item, str):
                        proxies_list.append(item)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Add proxies
            added = await self.add_proxies_bulk(proxies_list)
            logger.info(f"Imported {added} proxies from {file_path}")
            return added
            
        except Exception as e:
            logger.error(f"Error importing proxies: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        total = len(self.proxies_cache)
        active = len(self.active_proxies)
        
        type_counts = {}
        for proxy in self.proxies_cache:
            type_counts[proxy.proxy_type] = type_counts.get(proxy.proxy_type, 0) + 1
        
        # Calculate average speed and success rate for active proxies
        active_speeds = [p.speed for p in self.active_proxies if p.speed]
        avg_speed = sum(active_speeds) / len(active_speeds) if active_speeds else 0
        
        active_success_rates = [p.success_rate for p in self.active_proxies]
        avg_success_rate = sum(active_success_rates) / len(active_success_rates) if active_success_rates else 0
        
        # Recently tested (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recently_tested = len([
            p for p in self.proxies_cache 
            if p.last_tested and p.last_tested > recent_cutoff
        ])
        
        return {
            "total_proxies": total,
            "active_proxies": active,
            "inactive_proxies": total - active,
            "type_distribution": type_counts,
            "average_speed_ms": avg_speed,
            "average_success_rate": avg_success_rate,
            "recently_tested": recently_tested,
            "health_score": self._calculate_health_score(active, total, avg_success_rate)
        }
    
    async def search_proxies(
        self, 
        query: str = None, 
        proxy_type: str = None,
        min_success_rate: float = 0.0,
        max_speed: float = None
    ) -> List[ProxyInfo]:
        """Search proxies with filters"""
        results = self.proxies_cache
        
        # Filter by query (search in URL)
        if query:
            results = [p for p in results if query.lower() in p.url.lower()]
        
        # Filter by type
        if proxy_type:
            results = [p for p in results if p.proxy_type == proxy_type]
        
        # Filter by success rate
        if min_success_rate > 0:
            results = [p for p in results if p.success_rate >= min_success_rate]
        
        # Filter by speed
        if max_speed:
            results = [p for p in results if p.speed and p.speed <= max_speed]
        
        # Filter active only
        results = [p for p in results if p.is_active]
        
        return results
    
    async def backup_proxies(self) -> bool:
        """Create backup of proxies"""
        try:
            backup_file = PROXIES_DIR / f"backup/proxies_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await self.file_handler.create_directory(backup_file.parent)
            
            proxies_data = [proxy.to_dict() for proxy in self.proxies_cache]
            await self.file_handler.write_json(backup_file, proxies_data)
            
            logger.info(f"Created proxies backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _calculate_health_score(
        self, 
        active_count: int, 
        total_count: int, 
        avg_success_rate: float
    ) -> float:
        """Calculate proxy pool health score (0-100)"""
        if total_count == 0:
            return 0.0
        
        # Weighted score
        availability_score = (active_count / total_count) * 40  # 40% weight
        success_score = avg_success_rate * 60  # 60% weight
        
        return min(100.0, availability_score + success_score)
    
    def _get_proxy_id(self, proxy_url: str) -> Optional[int]:
        """Get database ID for proxy"""
        try:
            db = SessionLocal()
            # This would query by URL in real implementation
            # Simplified for now
            return None
        except Exception:
            return None
        finally:
            db.close()