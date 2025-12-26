"""
Method 3: Multiple Account Rotation
Uses many accounts to send views
"""

import asyncio
import aiohttp
import json
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class MultiAccountMethod:
    def __init__(self):
        self.name = "multi_account"
        self.success_rate = 95  # 95% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Account pool
        self.accounts = []
        self.active_accounts = []
        self.account_file = "accounts/accounts.json"
        
        # Async settings
        self.max_concurrent = 10
        self.session_timeout = 30
        
    def is_available(self) -> bool:
        """Check if method is available (has accounts)"""
        self.load_accounts()
        return len(self.accounts) > 0
    
    def load_accounts(self) -> int:
        """Load accounts from file"""
        try:
            with open(self.account_file, 'r') as f:
                self.accounts = json.load(f)
            
            # Filter active accounts
            self.active_accounts = [
                acc for acc in self.accounts 
                if acc.get('active', True) and acc.get('cookies')
            ]
            
            logger.info(f"Loaded {len(self.active_accounts)} active accounts")
            return len(self.active_accounts)
            
        except FileNotFoundError:
            logger.warning("No accounts file found")
            self.accounts = []
            self.active_accounts = []
            return 0
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            return 0
    
    def save_accounts(self):
        """Save accounts to file"""
        try:
            with open(self.account_file, 'w') as f:
                json.dump(self.accounts, f, indent=2)
            logger.info(f"Saved {len(self.accounts)} accounts to file")
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using multiple accounts"""
        logger.info(f"Multi-Account Method: Sending {view_count} views")
        
        if not self.active_accounts:
            self.load_accounts()
            if not self.active_accounts:
                return {
                    'method': self.name,
                    'requested_views': view_count,
                    'success_count': 0,
                    'failed_count': view_count,
                    'error': 'No active accounts available'
                }
        
        # Run async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                self.send_views_async(video_url, view_count)
            )
        finally:
            loop.close()
        
        self.last_used = time.time()
        self.total_views_sent += view_count
        self.successful_views += results['success_count']
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"Multi-Account Results: {results['success_count']}/{view_count} successful")
        return results
    
    async def send_views_async(self, video_url: str, view_count: int) -> Dict:
        """Async version of send_views"""
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'accounts_used': 0
        }
        
        # Create tasks
        tasks = []
        views_per_account = max(1, view_count // len(self.active_accounts))
        
        for i, account in enumerate(self.active_accounts[:self.max_concurrent]):
            account_views = min(views_per_account, view_count - results['success_count'])
            if account_views <= 0:
                break
            
            task = self.send_views_from_account(
                account, 
                video_url, 
                account_views
            )
            tasks.append(task)
        
        # Execute tasks
        if tasks:
            account_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in account_results:
                if isinstance(result, dict):
                    results['success_count'] += result.get('success', 0)
                    results['failed_count'] += result.get('failed', 0)
                    results['accounts_used'] += 1
        
        return results
    
    async def send_views_from_account(self, account: Dict, video_url: str, view_count: int) -> Dict:
        """Send views from a single account"""
        success = 0
        failed = 0
        
        try:
            cookies = self.parse_cookies(account.get('cookies', {}))
            
            async with aiohttp.ClientSession(
                cookies=cookies,
                headers=self.get_account_headers(account),
                timeout=aiohttp.ClientTimeout(total=self.session_timeout)
            ) as session:
                
                for i in range(view_count):
                    try:
                        # Visit video page
                        async with session.get(video_url) as response:
                            if response.status == 200:
                                # Read response to simulate loading
                                await response.text()
                                
                                # Simulate watching time
                                watch_time = random.randint(10, 30)
                                await asyncio.sleep(watch_time)
                                
                                # Random interactions
                                if random.random() < 0.3:
                                    await self.simulate_interactions(session, video_url)
                                
                                success += 1
                                logger.debug(f"Account {account.get('username', 'unknown')}: View {i+1} successful")
                            else:
                                failed += 1
                                logger.warning(f"Account {account.get('username')}: HTTP {response.status}")
                        
                        # Delay between views from same account
                        if i < view_count - 1:
                            await asyncio.sleep(random.uniform(3, 8))
                            
                    except Exception as e:
                        logger.error(f"Account {account.get('username')} view error: {e}")
                        failed += 1
        
        except Exception as e:
            logger.error(f"Account session error: {e}")
            failed = view_count
        
        # Update account stats
        self.update_account_stats(account, success)
        
        return {'success': success, 'failed': failed}
    
    def parse_cookies(self, cookies_data: Dict) -> Dict:
        """Parse cookies from account data"""
        cookies = {}
        
        if isinstance(cookies_data, dict):
            for key, value in cookies_data.items():
                if isinstance(value, str):
                    cookies[key] = value
                elif isinstance(value, dict) and 'value' in value:
                    cookies[key] = value['value']
        
        return cookies
    
    def get_account_headers(self, account: Dict) -> Dict:
        """Get headers for account"""
        headers = {
            "User-Agent": account.get('user_agent', 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Add device-specific headers
        device = account.get('device', {})
        if device.get('platform') == 'android':
            headers['X-Requested-With'] = 'com.zhiliaoapp.musically'
        elif device.get('platform') == 'ios':
            headers['X-Requested-With'] = 'TikTok'
        
        return headers
    
    async def simulate_interactions(self, session: aiohttp.ClientSession, video_url: str):
        """Simulate user interactions"""
        try:
            # Like action
            if random.random() < 0.2:
                like_url = video_url.replace('/video/', '/like/')
                async with session.post(like_url, data={'action': 'like'}):
                    await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Comment action (simulated)
            if random.random() < 0.1:
                await asyncio.sleep(random.uniform(1, 2))
        
        except:
            pass  # Silently fail interactions
    
    def update_account_stats(self, account: Dict, success_count: int):
        """Update account statistics"""
        try:
            # Find account in list
            for i, acc in enumerate(self.accounts):
                if acc.get('id') == account.get('id'):
                    # Update stats
                    if 'stats' not in self.accounts[i]:
                        self.accounts[i]['stats'] = {}
                    
                    stats = self.accounts[i]['stats']
                    stats['total_views'] = stats.get('total_views', 0) + success_count
                    stats['last_used'] = datetime.now().isoformat()
                    stats['success_rate'] = (
                        stats.get('success_rate', 0) * 0.8 + 
                        (success_count / max(1, success_count)) * 0.2
                    )
                    
                    # Mark as inactive if too many failures
                    if stats.get('failure_rate', 0) > 0.7:
                        self.accounts[i]['active'] = False
                    
                    break
            
            # Save periodically
            if random.random() < 0.1:  # 10% chance to save
                self.save_accounts()
        
        except Exception as e:
            logger.error(f"Error updating account stats: {e}")
    
    def add_account(self, account_data: Dict):
        """Add a new account"""
        # Generate ID if not present
        if 'id' not in account_data:
            account_data['id'] = f"acc_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Set default values
        account_data.setdefault('active', True)
        account_data.setdefault('created', datetime.now().isoformat())
        account_data.setdefault('stats', {
            'total_views': 0,
            'success_rate': 0
        })
        
        self.accounts.append(account_data)
        self.active_accounts.append(account_data)
        
        logger.info(f"Added new account: {account_data.get('username', 'unknown')}")
        self.save_accounts()
    
    def create_dummy_accounts(self, count: int = 10):
        """Create dummy accounts for testing"""
        for i in range(count):
            account = {
                'username': f'dummy_user_{random.randint(10000, 99999)}',
                'email': f'dummy{random.randint(10000, 99999)}@temp.com',
                'cookies': {
                    'sessionid': ''.join(random.choices('abcdef0123456789', k=32)),
                    'tt_chain_token': ''.join(random.choices('abcdef0123456789', k=64))
                },
                'user_agent': random.choice([
                    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"
                ]),
                'device': {
                    'platform': random.choice(['android', 'ios']),
                    'model': random.choice(['Pixel 4', 'iPhone 12', 'Samsung S21'])
                }
            }
            
            self.add_account(account)
        
        logger.info(f"Created {count} dummy accounts")
    
    def get_account_stats(self) -> Dict:
        """Get overall account statistics"""
        active = len(self.active_accounts)
        total = len(self.accounts)
        
        total_views = sum(
            acc.get('stats', {}).get('total_views', 0) 
            for acc in self.accounts
        )
        
        return {
            'total_accounts': total,
            'active_accounts': active,
            'inactive_accounts': total - active,
            'total_views_sent': total_views,
            'avg_success_rate': sum(
                acc.get('stats', {}).get('success_rate', 0) 
                for acc in self.active_accounts
            ) / max(active, 1)
        }
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup method"""
        self.save_accounts()