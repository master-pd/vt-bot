"""
Advanced View Sender
Professional TikTok view sending with multi-method support
"""

import asyncio
import random
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict

import aiohttp
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Browser, Page

from utils.logger import setup_logger
from utils.error_handler import handle_errors, retry, graceful
from core.account_manager import AccountManager
from core.proxy_manager import ProxyManager
from config import (
    MAX_CONCURRENT_REQUESTS, REQUEST_TIMEOUT,
    RETRY_ATTEMPTS, VIEWS_PER_MINUTE_LIMIT,
    Colors
)

logger = setup_logger(__name__)

@dataclass
class ViewResult:
    """View sending result"""
    success: bool
    view_id: str
    timestamp: datetime
    method_used: str
    proxy_used: Optional[str] = None
    account_used: Optional[str] = None
    response_time: float = 0.0
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ViewMethod:
    """View sending method base class"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.success_count = 0
        self.failure_count = 0
        self.total_time = 0.0
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100) if total > 0 else 0.0
    
    @property
    def average_time(self) -> float:
        """Calculate average response time"""
        total = self.success_count + self.failure_count
        return (self.total_time / total) if total > 0 else 0.0
    
    async def send_view(self, video_url: str, **kwargs) -> ViewResult:
        """Send a view (to be implemented by subclasses)"""
        raise NotImplementedError

class DirectRequestMethod(ViewMethod):
    """Direct HTTP request method"""
    
    def __init__(self):
        super().__init__("direct_request", priority=2)
        self.user_agent = UserAgent()
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @retry(max_retries=2, base_delay=1.0)
    @handle_errors(context="direct_request_method")
    async def send_view(self, video_url: str, **kwargs) -> ViewResult:
        """Send view using direct HTTP request"""
        await self.initialize()
        
        view_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        proxy = kwargs.get('proxy')
        account = kwargs.get('account')
        
        headers = {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            async with self.session.get(
                video_url,
                headers=headers,
                proxy=proxy,
                allow_redirects=True
            ) as response:
                
                response_time = time.time() - start_time
                self.total_time += response_time
                
                if response.status == 200:
                    # Simulate watching the video
                    await asyncio.sleep(random.uniform(3, 8))
                    
                    self.success_count += 1
                    return ViewResult(
                        success=True,
                        view_id=view_id,
                        timestamp=datetime.now(),
                        method_used=self.name,
                        proxy_used=proxy,
                        account_used=account,
                        response_time=response_time,
                        status_code=response.status
                    )
                else:
                    self.failure_count += 1
                    return ViewResult(
                        success=False,
                        view_id=view_id,
                        timestamp=datetime.now(),
                        method_used=self.name,
                        proxy_used=proxy,
                        account_used=account,
                        response_time=response_time,
                        error_message=f"HTTP {response.status}",
                        status_code=response.status
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            self.total_time += response_time
            self.failure_count += 1
            
            return ViewResult(
                success=False,
                view_id=view_id,
                timestamp=datetime.now(),
                method_used=self.name,
                proxy_used=proxy,
                account_used=account,
                response_time=response_time,
                error_message=str(e)
            )

class BrowserMethod(ViewMethod):
    """Browser automation method using Playwright"""
    
    def __init__(self):
        super().__init__("browser_automation", priority=1)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.user_agent = UserAgent()
        
    async def initialize(self):
        """Initialize browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        if not self.browser:
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
    
    @retry(max_retries=1, base_delay=2.0)
    @handle_errors(context="browser_method")
    async def send_view(self, video_url: str, **kwargs) -> ViewResult:
        """Send view using browser automation"""
        await self.initialize()
        
        view_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        proxy = kwargs.get('proxy')
        account = kwargs.get('account')
        
        try:
            # Create browser context with proxy if provided
            context_args = {
                'user_agent': self.user_agent.random,
                'viewport': {'width': 1920, 'height': 1080},
                'ignore_https_errors': True,
                'java_script_enabled': True,
            }
            
            if proxy:
                context_args['proxy'] = {'server': proxy}
            
            context = await self.browser.new_context(**context_args)
            
            # Create page
            page = await context.new_page()
            
            # Set extra headers to look more like a real browser
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.tiktok.com/',
                'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Navigate to video
            await page.goto(video_url, wait_until='networkidle', timeout=15000)
            
            # Wait for page to load
            await page.wait_for_timeout(3000)
            
            # Simulate human-like behavior
            await self._simulate_human_behavior(page)
            
            # Get page metrics
            response_time = time.time() - start_time
            self.total_time += response_time
            
            # Check if video is playing (basic check)
            video_playing = await self._check_video_playing(page)
            
            if video_playing:
                # Watch video for random time
                watch_time = random.uniform(5, 15)
                await page.wait_for_timeout(int(watch_time * 1000))
                
                self.success_count += 1
                result = ViewResult(
                    success=True,
                    view_id=view_id,
                    timestamp=datetime.now(),
                    method_used=self.name,
                    proxy_used=proxy,
                    account_used=account,
                    response_time=response_time
                )
            else:
                self.failure_count += 1
                result = ViewResult(
                    success=False,
                    view_id=view_id,
                    timestamp=datetime.now(),
                    method_used=self.name,
                    proxy_used=proxy,
                    account_used=account,
                    response_time=response_time,
                    error_message="Video not detected"
                )
            
            # Close context
            await context.close()
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self.total_time += response_time
            self.failure_count += 1
            
            return ViewResult(
                success=False,
                view_id=view_id,
                timestamp=datetime.now(),
                method_used=self.name,
                proxy_used=proxy,
                account_used=account,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def _simulate_human_behavior(self, page: Page):
        """Simulate human-like browsing behavior"""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1800)
                y = random.randint(100, 800)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.uniform(100, 500))
            
            # Random scrolls
            for _ in range(random.randint(1, 3)):
                scroll_amount = random.randint(100, 500)
                await page.mouse.wheel(0, scroll_amount)
                await page.wait_for_timeout(random.uniform(500, 1500))
            
            # Random clicks (if safe)
            if random.random() > 0.7:  # 30% chance
                elements = await page.query_selector_all('button, a')
                if elements:
                    safe_element = random.choice(elements)
                    try:
                        await safe_element.click(timeout=2000)
                        await page.wait_for_timeout(random.uniform(1000, 3000))
                    except:
                        pass
            
        except Exception:
            pass  # Ignore behavior simulation errors
    
    async def _check_video_playing(self, page: Page) -> bool:
        """Check if video is playing"""
        try:
            # Look for video elements
            video_elements = await page.query_selector_all('video')
            
            if video_elements:
                # Check if any video is likely playing
                for video in video_elements:
                    try:
                        # Check video properties
                        is_playing = await video.evaluate('''
                            element => {
                                return !element.paused && element.readyState >= 2;
                            }
                        ''')
                        
                        if is_playing:
                            return True
                    except:
                        continue
            
            # Alternative: Check for video containers
            video_containers = await page.query_selector_all(
                '[data-e2e="video-player"], .tiktok-video, video'
            )
            
            return len(video_containers) > 0
            
        except Exception:
            return False

class APIMethod(ViewMethod):
    """API-based method (if available)"""
    
    def __init__(self):
        super().__init__("api_method", priority=3)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @graceful(fallback_value=None)
    @handle_errors(context="api_method")
    async def send_view(self, video_url: str, **kwargs) -> ViewResult:
        """Send view using API (placeholder for future implementation)"""
        # This method is a placeholder for potential API-based approaches
        # Currently returns None to indicate it's not available
        
        return None

class ViewSender:
    """Advanced view sender with multiple methods"""
    
    def __init__(self, account_manager: AccountManager, proxy_manager: ProxyManager):
        self.account_manager = account_manager
        self.proxy_manager = proxy_manager
        
        # Initialize view methods
        self.methods: List[ViewMethod] = [
            BrowserMethod(),
            DirectRequestMethod(),
            APIMethod()
        ]
        
        self.active_methods: List[ViewMethod] = []
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.running = False
        self.stats = {
            'total_views_sent': 0,
            'total_views_failed': 0,
            'start_time': None,
            'views_per_minute': 0
        }
        
        # Rate limiting
        self.views_sent_this_minute = 0
        self.minute_start_time = time.time()
        
    async def initialize(self):
        """Initialize view sender"""
        logger.info("Initializing View Sender...")
        
        # Initialize account and proxy managers
        await self.account_manager.initialize()
        await self.proxy_manager.initialize()
        
        # Initialize view methods
        for method in self.methods:
            try:
                if hasattr(method, 'initialize'):
                    await method.initialize()
                self.active_methods.append(method)
                logger.info(f"Initialized view method: {method.name}")
            except Exception as e:
                logger.error(f"Failed to initialize method {method.name}: {e}")
        
        # Sort methods by priority (higher priority first)
        self.active_methods.sort(key=lambda m: m.priority, reverse=True)
        
        self.stats['start_time'] = time.time()
        self.running = True
        
        logger.info(f"View Sender initialized with {len(self.active_methods)} methods")
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up View Sender...")
        
        self.running = False
        
        # Cleanup methods
        for method in self.methods:
            try:
                if hasattr(method, 'cleanup'):
                    await method.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up method {method.name}: {e}")
        
        logger.info("View Sender cleanup complete")
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.minute_start_time >= 60:
            self.views_sent_this_minute = 0
            self.minute_start_time = current_time
        
        # Check limit
        if self.views_sent_this_minute >= VIEWS_PER_MINUTE_LIMIT:
            return False
        
        self.views_sent_this_minute += 1
        return True
    
    def _update_stats(self, success: bool):
        """Update statistics"""
        if success:
            self.stats['total_views_sent'] += 1
        else:
            self.stats['total_views_failed'] += 1
        
        # Calculate views per minute
        elapsed_minutes = (time.time() - self.stats['start_time']) / 60
        if elapsed_minutes > 0:
            total_views = self.stats['total_views_sent'] + self.stats['total_views_failed']
            self.stats['views_per_minute'] = total_views / elapsed_minutes
    
    def _select_method(self) -> ViewMethod:
        """Select the best method based on success rate"""
        if not self.active_methods:
            raise RuntimeError("No active view methods available")
        
        # Filter methods with recent activity
        active_methods = [
            m for m in self.active_methods 
            if m.success_count + m.failure_count > 0
        ]
        
        if not active_methods:
            # No method has been used yet, use highest priority
            return self.active_methods[0]
        
        # Select method based on success rate and response time
        best_method = max(
            active_methods,
            key=lambda m: (
                m.success_rate * 0.7 +  # 70% weight on success rate
                (100 / max(1, m.average_time)) * 0.3  # 30% weight on speed
            )
        )
        
        return best_method
    
    async def send_single_view(self, video_url: str) -> ViewResult:
        """Send a single view to video URL"""
        if not self.running:
            raise RuntimeError("View Sender is not running")
        
        # Check rate limit
        if not self._check_rate_limit():
            return ViewResult(
                success=False,
                view_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                method_used="rate_limited",
                error_message="Rate limit exceeded"
            )
        
        async with self.semaphore:
            # Get account and proxy
            account = await self.account_manager.get_next_account()
            proxy_info = await self.proxy_manager.get_next_proxy()
            
            proxy_url = proxy_info.url if proxy_info else None
            account_username = account.username if account else None
            
            # Select method
            method = self._select_method()
            
            logger.debug(
                f"Sending view using {method.name} | "
                f"Account: {account_username or 'None'} | "
                f"Proxy: {proxy_url[:30] if proxy_url else 'None'}"
            )
            
            # Send view
            result = await method.send_view(
                video_url,
                proxy=proxy_url,
                account=account_username
            )
            
            # Update statistics
            self._update_stats(result.success)
            
            # Update account and proxy stats
            if account and result.success:
                await self.account_manager.increment_account_views(account.username, result.success)
            
            if proxy_info:
                await self.proxy_manager.validate_proxy(proxy_info.url)
            
            # Log result
            if result.success:
                logger.info(
                    f"View sent successfully | "
                    f"Method: {method.name} | "
                    f"Time: {result.response_time:.2f}s"
                )
            else:
                logger.warning(
                    f"View failed | "
                    f"Method: {method.name} | "
                    f"Error: {result.error_message}"
                )
            
            return result
    
    async def send_batch_views(
        self, 
        video_url: str, 
        view_count: int,
        batch_size: int = 10
    ) -> List[ViewResult]:
        """Send multiple views in batches"""
        logger.info(f"Starting batch of {view_count} views to {video_url}")
        
        all_results = []
        completed = 0
        
        try:
            # Process in batches
            for batch_start in range(0, view_count, batch_size):
                if not self.running:
                    break
                
                batch_end = min(batch_start + batch_size, view_count)
                batch_size_current = batch_end - batch_start
                
                logger.info(
                    f"Processing batch {batch_start//batch_size + 1}/"
                    f"{(view_count + batch_size - 1)//batch_size} "
                    f"({completed}/{view_count} completed)"
                )
                
                # Create tasks for current batch
                tasks = []
                for i in range(batch_size_current):
                    task = asyncio.create_task(self.send_single_view(video_url))
                    tasks.append(task)
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"View task failed with exception: {result}")
                        all_results.append(
                            ViewResult(
                                success=False,
                                view_id=str(uuid.uuid4())[:8],
                                timestamp=datetime.now(),
                                method_used="error",
                                error_message=str(result)
                            )
                        )
                    else:
                        all_results.append(result)
                        if result.success:
                            completed += 1
                
                # Small delay between batches
                if batch_end < view_count:
                    await asyncio.sleep(random.uniform(0.5, 2.0))
            
            logger.info(f"Batch completed: {completed}/{view_count} successful views")
            
        except Exception as e:
            logger.error(f"Batch view sending failed: {e}")
        
        return all_results
    
    def get_method_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all methods"""
        stats_list = []
        
        for method in self.methods:
            stats_list.append({
                'name': method.name,
                'priority': method.priority,
                'success_count': method.success_count,
                'failure_count': method.failure_count,
                'success_rate': method.success_rate,
                'average_time': method.average_time,
                'total_requests': method.success_count + method.failure_count,
                'is_active': method in self.active_methods
            })
        
        return stats_list
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        total_views = self.stats['total_views_sent'] + self.stats['total_views_failed']
        
        return {
            **self.stats,
            'total_views': total_views,
            'success_rate': (
                (self.stats['total_views_sent'] / total_views * 100) 
                if total_views > 0 else 0.0
            ),
            'active_methods': len(self.active_methods),
            'rate_limit_remaining': max(0, VIEWS_PER_MINUTE_LIMIT - self.views_sent_this_minute),
            'running': self.running
        }
    
    async def test_all_methods(self, video_url: str) -> Dict[str, Any]:
        """Test all available view methods"""
        logger.info(f"Testing all methods with URL: {video_url}")
        
        test_results = {
            'video_url': video_url,
            'timestamp': datetime.now().isoformat(),
            'methods': []
        }
        
        for method in self.active_methods:
            try:
                logger.info(f"Testing method: {method.name}")
                
                # Get proxy for testing
                proxy_info = await self.proxy_manager.get_next_proxy()
                proxy_url = proxy_info.url if proxy_info else None
                
                # Test the method
                start_time = time.time()
                result = await method.send_view(video_url, proxy=proxy_url)
                test_time = time.time() - start_time
                
                test_results['methods'].append({
                    'name': method.name,
                    'priority': method.priority,
                    'success': result.success,
                    'response_time': result.response_time,
                    'total_test_time': test_time,
                    'error_message': result.error_message,
                    'status_code': result.status_code,
                    'proxy_used': proxy_url
                })
                
                logger.info(
                    f"Method {method.name}: "
                    f"{'Success' if result.success else 'Failed'} "
                    f"in {result.response_time:.2f}s"
                )
                
            except Exception as e:
                logger.error(f"Error testing method {method.name}: {e}")
                
                test_results['methods'].append({
                    'name': method.name,
                    'priority': method.priority,
                    'success': False,
                    'error_message': str(e),
                    'response_time': 0.0
                })
        
        # Determine best method
        successful_methods = [
            m for m in test_results['methods'] 
            if m['success']
        ]
        
        if successful_methods:
            best_method = min(successful_methods, key=lambda m: m['response_time'])
            test_results['best_method'] = best_method['name']
            test_results['best_response_time'] = best_method['response_time']
        else:
            test_results['best_method'] = None
            test_results['best_response_time'] = None
        
        return test_results