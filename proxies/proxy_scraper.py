"""
Proxy Scraper - Scrape proxies from various sources
"""

import requests
import re
import time
import random
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class ProxyScraper:
    def __init__(self):
        self.proxy_sources = [
            # Free proxy lists
            {
                'name': 'ProxyScrape',
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                'type': 'api',
                'format': 'text_lines'
            },
            {
                'name': 'FreeProxyList',
                'url': 'https://free-proxy-list.net/',
                'type': 'html',
                'format': 'table'
            },
            {
                'name': 'USProxy',
                'url': 'https://www.us-proxy.org/',
                'type': 'html',
                'format': 'table'
            },
            {
                'name': 'SSLProxies',
                'url': 'https://www.sslproxies.org/',
                'type': 'html',
                'format': 'table'
            },
            {
                'name': 'ProxyListDownload',
                'url': 'https://www.proxy-list.download/api/v1/get?type=http',
                'type': 'api',
                'format': 'text_lines'
            },
            {
                'name': 'Geonode',
                'url': 'https://proxylist.geonode.com/api/proxy-list?protocol=http&limit=500',
                'type': 'api',
                'format': 'json'
            },
            {
                'name': 'OpenProxy',
                'url': 'https://openproxy.space/list/http',
                'type': 'html',
                'format': 'text'
            },
            {
                'name': 'ProxyDaily',
                'url': 'http://www.proxydaily.com/',
                'type': 'html',
                'format': 'various'
            },
            {
                'name': 'HideMy',
                'url': 'https://hidemy.name/en/proxy-list/',
                'type': 'html',
                'format': 'table'
            },
            {
                'name': 'SpysOne',
                'url': 'https://spys.one/en/free-proxy-list/',
                'type': 'html',
                'format': 'complex'
            }
        ]
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Cache for recently scraped proxies
        self.proxy_cache = {}
        self.cache_timeout = 3600  # 1 hour
    
    def scrape_all_proxies(self, max_workers: int = 10) -> List[str]:
        """Scrape proxies from all sources"""
        logger.info("Scraping proxies from all sources...")
        
        all_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for source in self.proxy_sources:
                future = executor.submit(self.scrape_source, source)
                futures[future] = source['name']
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    proxies = future.result(timeout=30)
                    if proxies:
                        all_proxies.extend(proxies)
                        logger.info(f"Scraped {len(proxies)} proxies from {source_name}")
                    else:
                        logger.warning(f"No proxies from {source_name}")
                except Exception as e:
                    logger.error(f"Error scraping {source_name}: {e}")
        
        # Remove duplicates
        unique_proxies = list(set(all_proxies))
        
        logger.info(f"Total unique proxies scraped: {len(unique_proxies)}")
        
        # Cache results
        self.proxy_cache['all'] = {
            'proxies': unique_proxies,
            'timestamp': time.time()
        }
        
        return unique_proxies
    
    def scrape_source(self, source: Dict) -> List[str]:
        """Scrape proxies from a single source"""
        source_name = source['name']
        url = source['url']
        
        logger.debug(f"Scraping from {source_name}: {url}")
        
        try:
            # Check cache first
            cache_key = f"source_{source_name}"
            if cache_key in self.proxy_cache:
                cache_data = self.proxy_cache[cache_key]
                if time.time() - cache_data['timestamp'] < self.cache_timeout:
                    logger.debug(f"Using cached proxies for {source_name}")
                    return cache_data['proxies']
            
            # Make request
            response = requests.get(
                url,
                headers=self.headers,
                timeout=15,
                verify=False  # Some proxy sites have SSL issues
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {source_name}: HTTP {response.status_code}")
                return []
            
            # Parse based on source type
            if source['type'] == 'api':
                proxies = self.parse_api_response(response, source['format'])
            else:  # html
                proxies = self.parse_html_response(response, source['format'])
            
            # Cache results
            if proxies:
                self.proxy_cache[cache_key] = {
                    'proxies': proxies,
                    'timestamp': time.time()
                }
            
            return proxies
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout scraping {source_name}")
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error scraping {source_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            return []
    
    def parse_api_response(self, response, format_type: str) -> List[str]:
        """Parse API response for proxies"""
        proxies = []
        
        try:
            if format_type == 'text_lines':
                # One proxy per line: ip:port
                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if self.is_valid_proxy(line):
                        proxies.append(line)
            
            elif format_type == 'json':
                # JSON response
                data = response.json()
                
                # Try different JSON structures
                if 'data' in data and isinstance(data['data'], list):
                    for item in data['data']:
                        proxy = f"{item.get('ip')}:{item.get('port')}"
                        if self.is_valid_proxy(proxy):
                            proxies.append(proxy)
                
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            proxy = f"{item.get('ip')}:{item.get('port')}"
                            if self.is_valid_proxy(proxy):
                                proxies.append(proxy)
                        elif isinstance(item, str) and ':' in item:
                            if self.is_valid_proxy(item):
                                proxies.append(item)
                
        except Exception as e:
            logger.error(f"Error parsing API response: {e}")
        
        return proxies
    
    def parse_html_response(self, response, format_type: str) -> List[str]:
        """Parse HTML response for proxies"""
        proxies = []
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if format_type == 'table':
                # Find proxy tables
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            
                            if ip and port and ip.count('.') == 3:
                                proxy = f"{ip}:{port}"
                                if self.is_valid_proxy(proxy):
                                    proxies.append(proxy)
            
            elif format_type == 'text':
                # Extract IP:PORT patterns from text
                text = soup.get_text()
                
                # Regex for IP:PORT patterns
                ip_port_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b'
                matches = re.findall(ip_port_pattern, text)
                
                for match in matches:
                    if self.is_valid_proxy(match):
                        proxies.append(match)
            
            elif format_type == 'complex':
                # For complex sites like spys.one
                # Look for script tags with proxy data
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        # Look for IP addresses in script
                        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
                        port_pattern = r':(\d{1,5})'
                        
                        ips = re.findall(ip_pattern, script.string)
                        ports = re.findall(port_pattern, script.string)
                        
                        if ips and ports:
                            # Simple pairing (might need adjustment per site)
                            for ip, port in zip(ips[:len(ports)], ports):
                                proxy = f"{ip}:{port}"
                                if self.is_valid_proxy(proxy):
                                    proxies.append(proxy)
        
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
        
        return proxies
    
    def is_valid_proxy(self, proxy: str) -> bool:
        """Check if proxy string is valid"""
        if not proxy or ':' not in proxy:
            return False
        
        try:
            ip, port = proxy.split(':')
            
            # Check IP
            ip_parts = ip.split('.')
            if len(ip_parts) != 4:
                return False
            
            for part in ip_parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            # Check port
            if not port.isdigit():
                return False
            
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                return False
            
            # Additional checks
            if ip.startswith('0.'):
                return False  # Usually not valid
            
            # Check for local/reserved IPs
            if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.16.'):
                return False  # Private IP
            
            if ip.startswith('127.'):
                return False  # Loopback
            
            if ip.startswith('169.254.'):
                return False  # Link-local
            
            return True
            
        except:
            return False
    
    def scrape_with_filters(self, filters: Dict = None) -> List[str]:
        """Scrape proxies with filters"""
        if filters is None:
            filters = {}
        
        all_proxies = self.scrape_all_proxies()
        
        filtered_proxies = []
        for proxy in all_proxies:
            if self.matches_filters(proxy, filters):
                filtered_proxies.append(proxy)
        
        logger.info(f"Filtered {len(filtered_proxies)} proxies from {len(all_proxies)}")
        return filtered_proxies
    
    def matches_filters(self, proxy: str, filters: Dict) -> bool:
        """Check if proxy matches filters"""
        try:
            ip, port = proxy.split(':')
            port_num = int(port)
            
            # Country filter (would need geo-IP database)
            if 'country' in filters:
                # This would require IP geolocation
                pass
            
            # Port range filter
            if 'min_port' in filters and port_num < filters['min_port']:
                return False
            
            if 'max_port' in filters and port_num > filters['max_port']:
                return False
            
            # Anonymity filter (hard to determine from scraping)
            if 'anonymity' in filters:
                # Would need to test proxy
                pass
            
            # SSL filter
            if 'ssl' in filters:
                # Would need to test HTTPS support
                pass
            
            # Speed filter (would need to test)
            if 'min_speed' in filters:
                pass
            
            return True
            
        except:
            return False
    
    def get_source_stats(self) -> Dict:
        """Get statistics about proxy sources"""
        stats = {
            'total_sources': len(self.proxy_sources),
            'sources': [],
            'last_scrape': self.proxy_cache.get('all', {}).get('timestamp', 0)
        }
        
        for source in self.proxy_sources:
            source_stats = {
                'name': source['name'],
                'type': source['type'],
                'url': source['url']
            }
            
            # Check cache
            cache_key = f"source_{source['name']}"
            if cache_key in self.proxy_cache:
                cache_data = self.proxy_cache[cache_key]
                source_stats['last_scraped'] = cache_data['timestamp']
                source_stats['proxies_found'] = len(cache_data['proxies'])
            else:
                source_stats['last_scraped'] = 0
                source_stats['proxies_found'] = 0
            
            stats['sources'].append(source_stats)
        
        return stats
    
    def save_proxies_to_file(self, proxies: List[str], filename: str = "proxies/scraped_proxies.txt"):
        """Save proxies to file"""
        try:
            with open(filename, 'w') as f:
                for proxy in proxies:
                    f.write(f"{proxy}\n")
            
            logger.info(f"Saved {len(proxies)} proxies to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving proxies: {e}")
            return False
    
    def load_proxies_from_file(self, filename: str = "proxies/scraped_proxies.txt") -> List[str]:
        """Load proxies from file"""
        proxies = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and self.is_valid_proxy(proxy):
                        proxies.append(proxy)
            
            logger.info(f"Loaded {len(proxies)} proxies from {filename}")
        except FileNotFoundError:
            logger.warning(f"Proxy file not found: {filename}")
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
        
        return proxies
    
    def clean_proxy_list(self, proxies: List[str]) -> List[str]:
        """Clean and deduplicate proxy list"""
        # Remove invalid
        valid_proxies = [p for p in proxies if self.is_valid_proxy(p)]
        
        # Remove duplicates
        unique_proxies = list(set(valid_proxies))
        
        # Sort (optional)
        unique_proxies.sort()
        
        logger.info(f"Cleaned {len(proxies)} -> {len(unique_proxies)} proxies")
        
        return unique_proxies
    
    def scrape_continuously(self, interval: int = 3600):
        """Continuously scrape proxies at interval"""
        logger.info(f"Starting continuous proxy scraping every {interval} seconds")
        
        while True:
            try:
                proxies = self.scrape_all_proxies()
                
                # Save to file
                self.save_proxies_to_file(proxies)
                
                # Wait for next interval
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping continuous scraping")
                break
            except Exception as e:
                logger.error(f"Error in continuous scraping: {e}")
                time.sleep(300)  # Wait 5 minutes on error