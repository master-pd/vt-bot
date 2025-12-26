"""
Proxy Checker - Validate and test proxy functionality
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import json

logger = logging.getLogger(__name__)

class ProxyChecker:
    def __init__(self):
        self.test_urls = [
            "http://httpbin.org/ip",
            "http://httpbin.org/get",
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "http://icanhazip.com",
            "https://ident.me"
        ]
        
        # Test servers in different regions
        self.regional_test_urls = {
            'us': [
                "http://httpbin.org/ip",
                "https://api.ipify.org?format=json"
            ],
            'eu': [
                "http://eu.httpbin.org/ip",
                "https://eu.ident.me"
            ],
            'asia': [
                "http://asia.httpbin.org/ip",
                "https://asia.ident.me"
            ]
        }
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json,text/html,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        
        # Cache for proxy checks
        self.check_cache = {}
        self.cache_timeout = 1800  # 30 minutes
    
    def check_proxy(self, proxy: str, timeout: int = 10, test_tiktok: bool = False) -> Tuple[bool, Dict]:
        """
        Check if a proxy is working
        
        Returns:
            Tuple of (is_working: bool, details: Dict)
        """
        # Check cache first
        cache_key = f"check_{proxy}"
        if cache_key in self.check_cache:
            cache_data = self.check_cache[cache_key]
            if time.time() - cache_data['timestamp'] < self.cache_timeout:
                logger.debug(f"Using cached check for {proxy}")
                return cache_data['is_working'], cache_data['details']
        
        details = {
            'proxy': proxy,
            'response_time': 0,
            'ip_address': '',
            'country': '',
            'anonymity': 'unknown',
            'supports_https': False,
            'tested_at': time.time()
        }
        
        try:
            # Test with HTTP first
            http_working, http_details = self.test_proxy_http(proxy, timeout)
            
            if http_working:
                details.update(http_details)
                
                # Test HTTPS if HTTP works
                https_working, https_details = self.test_proxy_https(proxy, timeout)
                details['supports_https'] = https_working
                
                if https_working:
                    details.update(https_details)
            
            # Test TikTok accessibility if requested
            if test_tiktok and http_working:
                tiktok_working, tiktok_details = self.test_tiktok_access(proxy, timeout)
                details['tiktok_accessible'] = tiktok_working
                details.update(tiktok_details)
            
            # Check anonymity level
            if details.get('ip_address'):
                details['anonymity'] = self.check_anonymity(proxy, details['ip_address'])
            
            # Calculate overall working status
            is_working = http_working and details.get('ip_address', '') != ''
            
            # Cache results
            self.check_cache[cache_key] = {
                'is_working': is_working,
                'details': details,
                'timestamp': time.time()
            }
            
            return is_working, details
            
        except Exception as e:
            logger.error(f"Error checking proxy {proxy}: {e}")
            details['error'] = str(e)
            
            # Cache failure
            self.check_cache[cache_key] = {
                'is_working': False,
                'details': details,
                'timestamp': time.time()
            }
            
            return False, details
    
    def test_proxy_http(self, proxy: str, timeout: int) -> Tuple[bool, Dict]:
        """Test proxy with HTTP requests"""
        details = {}
        
        # Test multiple URLs
        test_urls = random.sample(self.test_urls, min(3, len(self.test_urls)))
        
        for url in test_urls:
            try:
                start_time = time.time()
                
                response = requests.get(
                    url,
                    proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                    headers=self.headers,
                    timeout=timeout,
                    verify=False
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    # Try to extract IP from response
                    ip_address = self.extract_ip_from_response(response)
                    
                    if ip_address:
                        details['ip_address'] = ip_address
                        details['response_time'] = response_time
                        details['test_url'] = url
                        
                        # Get country from IP (optional)
                        try:
                            country = self.get_ip_country(ip_address)
                            if country:
                                details['country'] = country
                        except:
                            pass
                        
                        return True, details
            
            except requests.exceptions.ProxyError:
                logger.debug(f"Proxy error for {proxy} on {url}")
            except requests.exceptions.ConnectTimeout:
                logger.debug(f"Connection timeout for {proxy} on {url}")
            except requests.exceptions.ReadTimeout:
                logger.debug(f"Read timeout for {proxy} on {url}")
            except requests.exceptions.SSLError:
                logger.debug(f"SSL error for {proxy} on {url}")
            except Exception as e:
                logger.debug(f"Error testing {proxy} on {url}: {e}")
        
        return False, details
    
    def test_proxy_https(self, proxy: str, timeout: int) -> Tuple[bool, Dict]:
        """Test proxy with HTTPS requests"""
        details = {}
        
        # Test HTTPS URLs
        https_urls = [url for url in self.test_urls if url.startswith('https://')]
        
        if not https_urls:
            return False, details
        
        for url in random.sample(https_urls, min(2, len(https_urls))):
            try:
                start_time = time.time()
                
                response = requests.get(
                    url,
                    proxies={'https': f'http://{proxy}'},
                    headers=self.headers,
                    timeout=timeout,
                    verify=True  # Verify SSL for HTTPS
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    details['https_response_time'] = response_time
                    details['https_test_url'] = url
                    return True, details
            
            except requests.exceptions.SSLError:
                logger.debug(f"HTTPS SSL error for {proxy}")
                return False, details
            except Exception as e:
                logger.debug(f"HTTPS error for {proxy}: {e}")
        
        return False, details
    
    def test_tiktok_access(self, proxy: str, timeout: int) -> Tuple[bool, Dict]:
        """Test if proxy can access TikTok"""
        details = {}
        
        tiktok_urls = [
            "https://www.tiktok.com",
            "https://www.tiktok.com/@tiktok",
            "https://www.tiktok.com/foryou"
        ]
        
        for url in tiktok_urls:
            try:
                start_time = time.time()
                
                response = requests.get(
                    url,
                    proxies={'https': f'http://{proxy}'},
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    timeout=timeout,
                    allow_redirects=True
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    details['tiktok_response_time'] = response_time
                    details['tiktok_url'] = url
                    
                    # Check if TikTok page loaded (basic check)
                    if 'tiktok' in response.text.lower():
                        details['tiktok_loaded'] = True
                        return True, details
                    else:
                        # Might be blocked or captcha
                        details['tiktok_loaded'] = False
                        details['possible_block'] = True
            
            except Exception as e:
                logger.debug(f"TikTok access error for {proxy}: {e}")
                details['tiktok_error'] = str(e)
        
        return False, details
    
    def extract_ip_from_response(self, response) -> Optional[str]:
        """Extract IP address from response"""
        try:
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                data = response.json()
                
                # Try different JSON structures
                if 'ip' in data:
                    return data['ip']
                elif 'origin' in data:
                    return data['origin']
                elif 'query' in data:
                    return data['query']
            
            # Try plain text response
            text = response.text.strip()
            
            # Check if it looks like an IP address
            import re
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            match = re.search(ip_pattern, text)
            
            if match:
                return match.group(0)
        
        except:
            pass
        
        return None
    
    def get_ip_country(self, ip_address: str) -> Optional[str]:
        """Get country for IP address (optional)"""
        try:
            # Free IP geolocation service
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('countryCode', '')
        
        except:
            pass
        
        return None
    
    def check_anonymity(self, proxy: str, detected_ip: str) -> str:
        """Check proxy anonymity level"""
        try:
            # Get real IP without proxy
            response = requests.get(
                "https://api.ipify.org?format=json",
                timeout=10
            )
            
            if response.status_code == 200:
                real_ip = response.json().get('ip', '')
                
                # Check headers that might leak info
                test_headers = self.test_proxy_headers(proxy)
                
                if real_ip == detected_ip:
                    return 'transparent'
                elif any(h in test_headers for h in ['VIA', 'X-FORWARDED-FOR']):
                    return 'anonymous'
                else:
                    return 'elite'
        
        except:
            pass
        
        return 'unknown'
    
    def test_proxy_headers(self, proxy: str) -> Dict:
        """Test what headers proxy adds"""
        try:
            response = requests.get(
                "http://httpbin.org/headers",
                proxies={'http': f'http://{proxy}'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('headers', {})
        
        except:
            pass
        
        return {}
    
    def check_proxies_batch(self, proxies: List[str], max_workers: int = 20, 
                           timeout: int = 10, test_tiktok: bool = False) -> Dict:
        """Check multiple proxies in parallel"""
        logger.info(f"Checking {len(proxies)} proxies with {max_workers} workers")
        
        results = {
            'working': [],
            'not_working': [],
            'total_checked': 0,
            'success_rate': 0
        }
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for proxy in proxies:
                future = executor.submit(
                    self.check_proxy,
                    proxy,
                    timeout,
                    test_tiktok
                )
                futures[future] = proxy
            
            completed = 0
            for future in as_completed(futures):
                proxy = futures[future]
                completed += 1
                
                try:
                    is_working, details = future.result(timeout=timeout + 5)
                    
                    if is_working:
                        results['working'].append({
                            'proxy': proxy,
                            'details': details
                        })
                    else:
                        results['not_working'].append({
                            'proxy': proxy,
                            'details': details
                        })
                
                except Exception as e:
                    logger.error(f"Error checking proxy {proxy}: {e}")
                    results['not_working'].append({
                        'proxy': proxy,
                        'error': str(e)
                    })
                
                # Log progress
                if completed % 10 == 0:
                    logger.info(f"Checked {completed}/{len(proxies)} proxies")
        
        results['total_checked'] = len(proxies)
        
        if len(proxies) > 0:
            results['success_rate'] = len(results['working']) / len(proxies)
        
        logger.info(f"Batch check complete: {len(results['working'])}/{len(proxies)} working "
                   f"({results['success_rate']:.1%})")
        
        return results
    
    def check_proxy_speed(self, proxy: str, test_count: int = 3) -> Dict:
        """Check proxy speed with multiple tests"""
        speed_results = {
            'proxy': proxy,
            'tests': [],
            'average_time': 0,
            'min_time': 0,
            'max_time': 0,
            'success_rate': 0
        }
        
        successful_tests = 0
        response_times = []
        
        for i in range(test_count):
            try:
                test_url = random.choice(self.test_urls)
                start_time = time.time()
                
                response = requests.get(
                    test_url,
                    proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    successful_tests += 1
                    
                    speed_results['tests'].append({
                        'test_number': i + 1,
                        'url': test_url,
                        'response_time': response_time,
                        'success': True
                    })
                else:
                    speed_results['tests'].append({
                        'test_number': i + 1,
                        'url': test_url,
                        'success': False,
                        'status_code': response.status_code
                    })
            
            except Exception as e:
                speed_results['tests'].append({
                    'test_number': i + 1,
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate statistics
        if response_times:
            speed_results['average_time'] = sum(response_times) / len(response_times)
            speed_results['min_time'] = min(response_times)
            speed_results['max_time'] = max(response_times)
        
        speed_results['success_rate'] = successful_tests / test_count if test_count > 0 else 0
        
        return speed_results
    
    def check_proxy_reliability(self, proxy: str, duration: int = 60, interval: int = 5) -> Dict:
        """Check proxy reliability over time"""
        reliability_results = {
            'proxy': proxy,
            'duration': duration,
            'interval': interval,
            'checks': [],
            'success_count': 0,
            'failure_count': 0,
            'reliability': 0
        }
        
        start_time = time.time()
        check_number = 0
        
        while time.time() - start_time < duration:
            check_number += 1
            
            try:
                is_working, details = self.check_proxy(proxy, timeout=interval-1)
                
                reliability_results['checks'].append({
                    'check_number': check_number,
                    'timestamp': time.time(),
                    'success': is_working,
                    'response_time': details.get('response_time', 0)
                })
                
                if is_working:
                    reliability_results['success_count'] += 1
                else:
                    reliability_results['failure_count'] += 1
            
            except Exception as e:
                reliability_results['checks'].append({
                    'check_number': check_number,
                    'timestamp': time.time(),
                    'success': False,
                    'error': str(e)
                })
                reliability_results['failure_count'] += 1
            
            # Wait for next check
            time_left = duration - (time.time() - start_time)
            if time_left > interval:
                time.sleep(interval)
            else:
                time.sleep(max(1, time_left))
        
        # Calculate reliability
        total_checks = reliability_results['success_count'] + reliability_results['failure_count']
        if total_checks > 0:
            reliability_results['reliability'] = reliability_results['success_count'] / total_checks
        
        return reliability_results
    
    def validate_proxy_format(self, proxy: str) -> bool:
        """Validate proxy format"""
        try:
            # Check format: ip:port or ip:port:username:password
            parts = proxy.split(':')
            
            if len(parts) not in [2, 4]:
                return False
            
            # Validate IP
            ip = parts[0]
            ip_parts = ip.split('.')
            
            if len(ip_parts) != 4:
                return False
            
            for part in ip_parts:
                if not part.isdigit():
                    return False
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            # Validate port
            port = parts[1]
            if not port.isdigit():
                return False
            
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                return False
            
            # Validate credentials if present
            if len(parts) == 4:
                username = parts[2]
                password = parts[3]
                
                if not username or not password:
                    return False
            
            return True
        
        except:
            return False
    
    def cleanup_cache(self):
        """Cleanup old cache entries"""
        current_time = time.time()
        removed_count = 0
        
        keys_to_remove = []
        for key, data in self.check_cache.items():
            if current_time - data['timestamp'] > self.cache_timeout:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.check_cache[key]
            removed_count += 1
        
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} cache entries")
    
    def get_check_stats(self) -> Dict:
        """Get statistics about proxy checks"""
        total_checks = len(self.check_cache)
        
        working_count = sum(1 for data in self.check_cache.values() if data['is_working'])
        not_working_count = total_checks - working_count
        
        avg_response_time = 0
        response_times = []
        
        for data in self.check_cache.values():
            if data['is_working'] and 'details' in data:
                rt = data['details'].get('response_time', 0)
                if rt > 0:
                    response_times.append(rt)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'total_cached_checks': total_checks,
            'working_proxies_cached': working_count,
            'not_working_proxies_cached': not_working_count,
            'cache_success_rate': working_count / total_checks if total_checks > 0 else 0,
            'average_response_time': avg_response_time,
            'cache_timeout_seconds': self.cache_timeout
        }