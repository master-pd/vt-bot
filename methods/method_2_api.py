"""
Method 2: Direct API Calls to TikTok
Faster but less reliable than browser method
"""

import requests
import json
import time
import random
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class APIMethod:
    def __init__(self):
        self.name = "api_direct"
        self.success_rate = 70  # 70% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        self.api_endpoints = [
            "https://api.tiktok.com/api/item/detail/",
            "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/aweme/detail/",
            "https://api19-core-c-useast1a.tiktokv.com/aweme/v1/aweme/stats/",
            "https://api.tiktok.com/aweme/v1/aweme/stats/"
        ]
        
        # Common headers
        self.headers_list = [
            {
                "User-Agent": "com.ss.android.ugc.trill/2613 (Linux; U; Android 10; en_US; Pixel 4; Build/QQ3A.200805.001; Cronet/58.0.2991.0)",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Tt-Token": ""
            },
            {
                "User-Agent": "TikTok 26.1.3 rv:261103 (iPhone; iOS 14.6; en_US) Cronet",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        ]
    
    def is_available(self) -> bool:
        """Check if API method is available"""
        try:
            # Test API connectivity
            test_response = requests.get(
                "https://api.tiktok.com/api/item/detail/",
                timeout=10
            )
            return test_response.status_code != 403
        except:
            return False
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using direct API calls"""
        logger.info(f"API Method: Sending {view_count} views to {video_url}")
        
        # Extract video ID
        video_id = self.extract_video_id(video_url)
        if not video_id:
            return {
                'method': self.name,
                'requested_views': view_count,
                'success_count': 0,
                'failed_count': view_count,
                'error': 'Could not extract video ID'
            }
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'video_id': video_id
        }
        
        # Send views in batches
        batch_size = min(10, view_count)
        batches = (view_count + batch_size - 1) // batch_size
        
        for batch_num in range(batches):
            current_batch = min(batch_size, view_count - (batch_num * batch_size))
            
            batch_results = self.send_batch(video_id, current_batch)
            results['success_count'] += batch_results['success']
            results['failed_count'] += batch_results['failed']
            
            # Delay between batches
            if batch_num < batches - 1:
                time.sleep(random.uniform(5, 10))
        
        self.last_used = time.time()
        self.total_views_sent += view_count
        self.successful_views += results['success_count']
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"API Method Results: {results['success_count']}/{view_count} successful")
        return results
    
    def extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from TikTok URL"""
        try:
            # Handle different URL formats
            if "tiktok.com/@" in video_url:
                # Example: https://www.tiktok.com/@username/video/1234567890123456789
                parts = video_url.split('/')
                for i, part in enumerate(parts):
                    if part == 'video' and i + 1 < len(parts):
                        return parts[i + 1].split('?')[0]
            
            elif "vm.tiktok.com" in video_url or "vt.tiktok.com" in video_url:
                # Short URL - need to resolve
                try:
                    response = requests.head(video_url, allow_redirects=True, timeout=10)
                    resolved_url = response.url
                    return self.extract_video_id(resolved_url)
                except:
                    pass
            
            # Try to get from query parameters
            parsed = urlparse(video_url)
            query_params = parse_qs(parsed.query)
            
            if 'video_id' in query_params:
                return query_params['video_id'][0]
            elif 'id' in query_params:
                return query_params['id'][0]
            
            # Last resort: get from path
            path_parts = parsed.path.split('/')
            for part in path_parts:
                if part.isdigit() and len(part) > 15:
                    return part
        
        except Exception as e:
            logger.error(f"Error extracting video ID: {e}")
        
        return None
    
    def send_batch(self, video_id: str, batch_size: int) -> Dict:
        """Send a batch of views via API"""
        success = 0
        failed = 0
        
        for i in range(batch_size):
            try:
                if self.send_single_view_api(video_id):
                    success += 1
                else:
                    failed += 1
                
                # Random delay between API calls
                if i < batch_size - 1:
                    time.sleep(random.uniform(0.5, 2))
                    
            except Exception as e:
                logger.error(f"API call failed: {e}")
                failed += 1
        
        return {'success': success, 'failed': failed}
    
    def send_single_view_api(self, video_id: str) -> bool:
        """Send single view via TikTok API"""
        try:
            # Choose random endpoint and headers
            endpoint = random.choice(self.api_endpoints)
            headers = random.choice(self.headers_list)
            
            # Generate random device ID
            device_id = ''.join(random.choices('0123456789abcdef', k=16))
            
            # Prepare payload
            payload = {
                "item_id": video_id,
                "count": 1,
                "from": random.choice(["feed", "following", "profile", "hashtag"]),
                "source": random.choice(["video", "music", "effect", "challenge"]),
                "action_type": 1,  # 1 = view action
                "device_id": device_id,
                "os_version": random.choice(["10", "11", "12", "13", "14"]),
                "version_code": random.choice(["260000", "261000", "262000"]),
                "app_name": "trill",
                "device_type": random.choice(["Pixel 4", "iPhone 12", "Samsung Galaxy S21"]),
                "aid": random.choice([1180, 1233, 1234]),
                "channel": random.choice(["googleplay", "appstore"]),
                "device_platform": random.choice(["android", "ios"]),
                "ts": int(time.time()),
                "refer": "feed",
                "share_user_id": "",
                "object_id": video_id,
                "object_type": 0,
                "stats_channel": "video"
            }
            
            # Add random extra parameters
            if random.random() < 0.3:
                payload["play_delta"] = random.randint(1, 30)
            if random.random() < 0.2:
                payload["watch_time"] = random.randint(10, 60)
            
            # Make API request
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if view was registered
                if self.is_view_successful(response_data):
                    logger.debug(f"API view successful for video {video_id}")
                    return True
                else:
                    logger.debug(f"API view not registered for video {video_id}")
                    return False
            else:
                logger.warning(f"API returned status {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            return False
    
    def is_view_successful(self, response_data: dict) -> bool:
        """Check if API response indicates successful view"""
        try:
            # Check different response formats
            if isinstance(response_data, dict):
                # Check for success status
                if response_data.get('status_code') == 0:
                    return True
                
                # Check for view count
                if 'aweme_detail' in response_data:
                    aweme = response_data['aweme_detail']
                    if 'statistics' in aweme:
                        stats = aweme['statistics']
                        if 'play_count' in stats:
                            return True
                
                # Check for extra data
                if 'extra' in response_data:
                    extra = response_data['extra']
                    if 'now' in extra or 'logid' in extra:
                        return True
                
                # Simple success check
                if 'success' in response_data and response_data['success']:
                    return True
            
            return False
        
        except:
            return False
    
    def get_device_info(self) -> dict:
        """Generate random device information"""
        devices = [
            {
                "device_id": ''.join(random.choices('0123456789abcdef', k=16)),
                "device_type": "Pixel 4",
                "os_version": "10",
                "app_version": "26.1.3"
            },
            {
                "device_id": ''.join(random.choices('0123456789abcdef', k=16)),
                "device_type": "iPhone 12",
                "os_version": "14.6",
                "app_version": "26.1.3"
            },
            {
                "device_id": ''.join(random.choices('0123456789abcdef', k=16)),
                "device_type": "Samsung Galaxy S21",
                "os_version": "11",
                "app_version": "26.0.0"
            }
        ]
        return random.choice(devices)
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate