"""
View Sender - Handles sending views using different methods
"""

import time
import random
import asyncio
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from utils.logger import setup_logger
from methods.method_1_browser import BrowserMethod
from methods.method_2_api import APIMethod
from methods.method_3_multi_account import MultiAccountMethod
from methods.method_6_mobile_emulate import MobileEmulationMethod

logger = setup_logger(__name__)

class ViewSender:
    def __init__(self):
        self.methods = {
            'browser': BrowserMethod(),
            'api': APIMethod(),
            'multi_account': MultiAccountMethod(),
            'mobile': MobileEmulationMethod()
        }
        
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.active_tasks = []
    
    def send_views(self, video_url: str, view_count: int, method: str = "auto") -> Dict:
        """
        Send views to a TikTok video
        
        Args:
            video_url: URL of the TikTok video
            view_count: Number of views to send
            method: Method to use (auto, browser, api, multi_account, mobile)
        
        Returns:
            Dictionary with results
        """
        logger.info(f"Sending {view_count} views to {video_url} using method: {method}")
        
        start_time = time.time()
        results = {
            'success': False,
            'views_sent': 0,
            'views_failed': 0,
            'method_used': method,
            'time_taken': 0,
            'error': None
        }
        
        try:
            if method == "auto":
                method = self.select_best_method()
            
            if method in self.methods:
                # Split views into batches
                batches = self.create_batches(view_count)
                
                # Send views in parallel
                futures = []
                for batch in batches:
                    future = self.executor.submit(
                        self.send_batch,
                        video_url,
                        batch,
                        method
                    )
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    batch_result = future.result()
                    results['views_sent'] += batch_result.get('success', 0)
                    results['views_failed'] += batch_result.get('failed', 0)
                
                results['success'] = results['views_sent'] > 0
                
            else:
                results['error'] = f"Unknown method: {method}"
                logger.error(results['error'])
        
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error sending views: {e}")
        
        finally:
            results['time_taken'] = time.time() - start_time
            logger.info(f"View sending completed: {results['views_sent']}/{view_count} successful")
        
        return results
    
    def select_best_method(self) -> str:
        """Select the best method based on current conditions"""
        # Simple heuristic - could be enhanced with ML
        methods = list(self.methods.keys())
        
        # Check each method's availability
        available_methods = []
        for method_name, method_obj in self.methods.items():
            if method_obj.is_available():
                available_methods.append(method_name)
        
        if available_methods:
            # Prefer browser method for reliability
            if 'browser' in available_methods:
                return 'browser'
            elif 'mobile' in available_methods:
                return 'mobile'
            else:
                return random.choice(available_methods)
        
        return 'browser'  # Fallback
    
    def create_batches(self, total_views: int, max_batch_size: int = 10) -> List[int]:
        """Split total views into batches"""
        batches = []
        remaining = total_views
        
        while remaining > 0:
            batch_size = min(max_batch_size, remaining)
            batches.append(batch_size)
            remaining -= batch_size
        
        return batches
    
    def send_batch(self, video_url: str, batch_size: int, method: str) -> Dict:
        """Send a batch of views"""
        method_obj = self.methods.get(method)
        if not method_obj:
            return {'success': 0, 'failed': batch_size}
        
        try:
            result = method_obj.send_views(video_url, batch_size)
            return {
                'success': result.get('success_count', 0),
                'failed': batch_size - result.get('success_count', 0)
            }
        except Exception as e:
            logger.error(f"Error in batch sending: {e}")
            return {'success': 0, 'failed': batch_size}
    
    async def send_views_async(self, video_url: str, view_count: int, method: str = "auto"):
        """Async version of send_views"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.send_views,
            video_url,
            view_count,
            method
        )
    
    def get_method_stats(self) -> Dict:
        """Get statistics for each method"""
        stats = {}
        for method_name, method_obj in self.methods.items():
            stats[method_name] = {
                'available': method_obj.is_available(),
                'success_rate': method_obj.get_success_rate(),
                'last_used': method_obj.last_used,
                'total_views_sent': method_obj.total_views_sent
            }
        return stats
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        for method_obj in self.methods.values():
            if hasattr(method_obj, 'cleanup'):
                method_obj.cleanup()
        
        logger.info("ViewSender cleanup completed")