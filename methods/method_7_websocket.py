"""
Method 7: WebSocket Method - Real-time connection to TikTok
"""

import asyncio
import json
import time
import random
import logging
from typing import Dict, Optional
import websockets
import aiohttp

logger = logging.getLogger(__name__)

class WebSocketMethod:
    def __init__(self):
        self.name = "websocket"
        self.success_rate = 65  # 65% success rate (experimental)
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # WebSocket endpoints (these might change)
        self.ws_endpoints = [
            "wss://webcast.tiktok.com/ws/",
            "wss://webcast.tiktok.com/webcast/",
            "wss://webcast16-normal-c-useast1a.tiktok.com/ws/",
            "wss://webcast16-normal-c-useast2a.tiktok.com/ws/"
        ]
        
        # TikTok WebSocket message templates
        self.message_templates = {
            'view': {
                'type': 'View',
                'data': {
                    'video_id': '',
                    'viewer_id': '',
                    'timestamp': 0,
                    'duration': 0,
                    'position': 0
                }
            },
            'heartbeat': {
                'type': 'Heartbeat',
                'data': {
                    'timestamp': 0,
                    'interval': 30000
                }
            },
            'join': {
                'type': 'JoinRoom',
                'data': {
                    'room_id': '',
                    'user_id': ''
                }
            }
        }
    
    def is_available(self) -> bool:
        """Check if WebSocket method is available"""
        # WebSocket should always be available
        return True
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using WebSocket"""
        logger.info(f"WebSocket Method: Sending {view_count} views")
        
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
        
        logger.info(f"WebSocket Results: {results['success_count']}/{view_count} successful")
        return results
    
    async def send_views_async(self, video_url: str, view_count: int) -> Dict:
        """Async version of send_views"""
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0
        }
        
        # Extract video/room ID
        video_id = self.extract_video_id(video_url)
        if not video_id:
            results['failed_count'] = view_count
            return results
        
        # Create tasks for concurrent WebSocket connections
        tasks = []
        for i in range(min(view_count, 10)):  # Limit concurrent connections
            task = self.websocket_view(video_id, i)
            tasks.append(task)
        
        # Run tasks
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in task_results:
                if isinstance(result, bool) and result:
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
        
        # If we need more views, run in batches
        remaining_views = view_count - results['success_count'] - results['failed_count']
        
        while remaining_views > 0:
            batch_size = min(remaining_views, 10)
            
            batch_tasks = []
            for i in range(batch_size):
                task = self.websocket_view(video_id, i)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, bool) and result:
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
            
            remaining_views -= batch_size
            
            # Delay between batches
            if remaining_views > 0:
                await asyncio.sleep(random.uniform(5, 10))
        
        return results
    
    async def websocket_view(self, video_id: str, viewer_id: int) -> bool:
        """Establish WebSocket connection and send view"""
        ws_url = random.choice(self.ws_endpoints)
        
        try:
            async with websockets.connect(
                ws_url,
                timeout=30,
                extra_headers=self.get_ws_headers()
            ) as websocket:
                
                logger.debug(f"WebSocket connected: {ws_url}")
                
                # Send join message
                join_msg = self.create_message('join', {
                    'room_id': video_id,
                    'user_id': f'viewer_{viewer_id}_{int(time.time())}'
                })
                
                await websocket.send(json.dumps(join_msg))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)
                
                # Check if join successful
                if self.is_join_successful(response_data):
                    logger.debug(f"Joined room {video_id}")
                    
                    # Send view message
                    view_msg = self.create_message('view', {
                        'video_id': video_id,
                        'viewer_id': f'viewer_{viewer_id}',
                        'timestamp': int(time.time() * 1000),
                        'duration': random.randint(15000, 45000),  # 15-45 seconds
                        'position': random.randint(0, 100)
                    })
                    
                    await websocket.send(json.dumps(view_msg))
                    
                    # Send heartbeat periodically
                    for _ in range(random.randint(3, 8)):
                        heartbeat_msg = self.create_message('heartbeat', {
                            'timestamp': int(time.time() * 1000),
                            'interval': 30000
                        })
                        
                        await websocket.send(json.dumps(heartbeat_msg))
                        await asyncio.sleep(random.uniform(5, 15))
                    
                    # Close connection
                    await websocket.close()
                    
                    return True
                else:
                    logger.debug(f"Failed to join room {video_id}")
                    return False
        
        except asyncio.TimeoutError:
            logger.debug("WebSocket connection timeout")
            return False
        except websockets.exceptions.ConnectionClosed:
            logger.debug("WebSocket connection closed")
            return False
        except Exception as e:
            logger.debug(f"WebSocket error: {e}")
            return False
    
    def extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video/room ID from URL"""
        try:
            # Try different patterns
            if "/video/" in video_url:
                parts = video_url.split("/video/")
                if len(parts) > 1:
                    video_id = parts[1].split("?")[0]
                    return video_id
            
            # Try live URL pattern
            if "/live/" in video_url:
                parts = video_url.split("/live/")
                if len(parts) > 1:
                    room_id = parts[1].split("?")[0]
                    return room_id
            
            # Try to get from TikTok API
            return self.get_video_id_from_api(video_url)
            
        except:
            return None
    
    async def get_video_id_from_api(self, video_url: str) -> Optional[str]:
        """Get video ID from TikTok API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Look for video ID in HTML
                        import re
                        
                        patterns = [
                            r'"video_id":"(\d+)"',
                            r'"id":"(\d+)"',
                            r'video/(\d+)',
                            r'itemId":"(\d+)"'
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, html)
                            if match:
                                return match.group(1)
            
            return None
        except:
            return None
    
    def create_message(self, msg_type: str, data: dict) -> dict:
        """Create WebSocket message"""
        if msg_type in self.message_templates:
            message = self.message_templates[msg_type].copy()
            message['data'].update(data)
            message['timestamp'] = int(time.time() * 1000)
            message['msg_id'] = f"msg_{int(time.time())}_{random.randint(1000, 9999)}"
            return message
        
        # Default message
        return {
            'type': 'Unknown',
            'data': data,
            'timestamp': int(time.time() * 1000),
            'msg_id': f"msg_{int(time.time())}_{random.randint(1000, 9999)}"
        }
    
    def get_ws_headers(self) -> dict:
        """Get WebSocket headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://www.tiktok.com',
            'Host': 'webcast.tiktok.com',
            'Connection': 'Upgrade',
            'Upgrade': 'websocket',
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Key': self.generate_websocket_key(),
            'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits'
        }
    
    def generate_websocket_key(self) -> str:
        """Generate WebSocket key"""
        import base64
        import os
        key = base64.b64encode(os.urandom(16)).decode()
        return key
    
    def is_join_successful(self, response_data: dict) -> bool:
        """Check if join was successful"""
        try:
            if isinstance(response_data, dict):
                # Check for success status
                if response_data.get('type') == 'JoinSuccess':
                    return True
                
                # Check for room info
                if 'data' in response_data and 'room' in response_data['data']:
                    return True
                
                # Check for welcome message
                if response_data.get('msg') == 'Welcome':
                    return True
            
            return False
        except:
            return False
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup method"""
        pass