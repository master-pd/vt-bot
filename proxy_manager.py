"""
Proxy Manager - Handles proxy scraping, validation, and rotation
"""

import requests
import threading
import time
import random
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.active_proxies = []
        self.bad_proxies = []
        self.proxy_sources = [
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://openproxy.space/list/http",
            "https://proxylist.geonode.com/api/proxy-list?protocol=http&limit=50",
            "https://www.freeproxychecker.com/result/ proxies.txt"
        ]
        
        self.lock = threading.Lock()
        self.last_update = None
        self.check_interval = 3600  # 1 hour
        self.max_proxies = 500
    
    def load_proxies(self) -> int:
        """Load proxies from file and online sources"""
        logger.info("Loading proxies...")
        
        # Load from file
        file_proxies = self.load_from_file()
        self.proxies.extend(file_proxies)
        
        # Scrape online proxies
        online_proxies = self.scrape_online_proxies()
        self.proxies.extend(online_proxies)
        
        # Remove duplicates
        self.proxies = list(set(self.proxies))
        
        # Validate proxies
        self.validate_proxies()
        
        logger.info(f"Total proxies loaded: {len(self.proxies)}")
        logger.info(f"Active proxies: {len(self.active_proxies)}")
        
        self.last_update = time.time()
        return len(self.active_proxies)
    
    def load_from_file(self) -> List[str]:
        """Load proxies from proxies.txt file"""
        proxies = []
        try:
            with open('proxies/proxies.txt', 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and ':' in proxy:
                        proxies.append(proxy)
            logger.info(f"Loaded {len(proxies)} proxies from file")
        except FileNotFoundError:
            logger.warning("proxies.txt not found")
        
        return proxies
    
    def scrape_online_proxies(self) -> List[str]:
        """Scrape proxies from online sources"""
        all_proxies = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for source in self.proxy_sources:
                future = executor.submit(self.fetch_from_source, source)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    proxies = future.result(timeout=10)
                    all_proxies.extend(proxies)
                except Exception as e:
                    logger.error(f"Error fetching from source: {e}")
        
        # Remove duplicates
        all_proxies = list(set(all_proxies))
        logger.info(f"Scraped {len(all_proxies)} proxies online")
        
        return all_proxies
    
    def fetch_from_source(self, url: str) -> List[str]:
        """Fetch proxies from a single source"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                proxies = []
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line and ':' in line and not line.startswith('#'):
                        # Format: ip:port
                        if line.count(':') == 1:
                            proxies.append(line)
                        # Format: ip:port:username:password
                        elif line.count(':') == 3:
                            parts = line.split(':')
                            proxies.append(f"{parts[0]}:{parts[1]}")
                
                return proxies
        
        except Exception as e:
            logger.error(f"Error fetching from {url}: {e}")
        
        return []
    
    def validate_proxies(self, max_workers: int = 20):
        """Validate all proxies"""
        logger.info("Validating proxies...")
        
        self.active_proxies = []
        self.bad_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.check_proxy, proxy): proxy for proxy in self.proxies}
            
            for future in as_completed(futures):
                proxy = futures[future]
                try:
                    is_valid, response_time = future.result(timeout=10)
                    if is_valid:
                        with self.lock:
                            self.active_proxies.append({
                                'proxy': proxy,
                                'response_time': response_time,
                                'last_checked': time.time(),
                                'success_count': 0,
                                'fail_count': 0
                            })
                    else:
                        self.bad_proxies.append(proxy)
                except Exception as e:
                    logger.error(f"Error checking proxy {proxy}: {e}")
                    self.bad_proxies.append(proxy)
        
        # Sort by response time (fastest first)
        self.active_proxies.sort(key=lambda x: x['response_time'])
        
        logger.info(f"Valid proxies: {len(self.active_proxies)}")
        logger.info(f"Invalid proxies: {len(self.bad_proxies)}")
    
    def check_proxy(self, proxy: str) -> tuple:
        """Check if a proxy is working"""
        test_url = "https://httpbin.org/ip"
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        try:
            start_time = time.time()
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Verify proxy is actually being used
                data = response.json()
                if 'origin' in data:
                    return True, response_time
        
        except Exception:
            pass
        
        return False, 999
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Get a random working proxy"""
        if not self.active_proxies:
            logger.warning("No active proxies available")
            return None
        
        with self.lock:
            # Weighted random selection (faster proxies have higher chance)
            weights = [1 / (p['response_time'] + 0.1) for p in self.active_proxies]
            proxy_info = random.choices(self.active_proxies, weights=weights, k=1)[0]
            
            # Update success count
            proxy_info['success_count'] += 1
            proxy_info['last_used'] = time.time()
            
            return proxy_info
    
    def mark_proxy_bad(self, proxy_info: Dict):
        """Mark a proxy as bad"""
        with self.lock:
            if proxy_info in self.active_proxies:
                self.active_proxies.remove(proxy_info)
                self.bad_proxies.append(proxy_info['proxy'])
                logger.warning(f"Marked proxy {proxy_info['proxy']} as bad")
    
    def save_proxies_to_file(self):
        """Save active proxies to file"""
        try:
            with open('proxies/proxies.txt', 'w') as f:
                for proxy_info in self.active_proxies:
                    f.write(f"{proxy_info['proxy']}\n")
            
            logger.info(f"Saved {len(self.active_proxies)} proxies to file")
        except Exception as e:
            logger.error(f"Error saving proxies: {e}")
    
    def background_checker(self):
        """Background thread to periodically check proxies"""
        while True:
            time.sleep(self.check_interval)
            
            logger.info("Running periodic proxy check...")
            self.validate_proxies()
            self.save_proxies_to_file()
            
            # Remove old bad proxies
            if len(self.bad_proxies) > 1000:
                self.bad_proxies = self.bad_proxies[-500:]
    
    def get_stats(self) -> Dict:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self.proxies),
            'active_proxies': len(self.active_proxies),
            'bad_proxies': len(self.bad_proxies),
            'last_update': self.last_update,
            'avg_response_time': sum(p['response_time'] for p in self.active_proxies) / max(len(self.active_proxies), 1)
        }
    
    def add_proxy(self, proxy: str):
        """Add a new proxy manually"""
        with self.lock:
            if proxy not in self.proxies:
                self.proxies.append(proxy)
                
                # Check it immediately
                is_valid, response_time = self.check_proxy(proxy)
                if is_valid:
                    self.active_proxies.append({
                        'proxy': proxy,
                        'response_time': response_time,
                        'last_checked': time.time(),
                        'success_count': 0,
                        'fail_count': 0
                    })
                    logger.info(f"Added new proxy: {proxy}")
                else:
                    self.bad_proxies.append(proxy)
                    logger.warning(f"Added proxy {proxy} but it's not working")