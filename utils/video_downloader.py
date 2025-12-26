"""
Video Downloader - Download TikTok videos for analysis
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Tuple
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, download_dir: str = "temp/videos"):
        self.download_dir = download_dir
        self.ensure_directory()
        
        # TikTok API endpoints (for video information)
        self.api_endpoints = {
            'video_info': 'https://api.tiktok.com/api/item/detail/',
            'video_url': 'https://api.tiktok.com/api/video/play/'
        }
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json,text/html,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
            'Origin': 'https://www.tiktok.com'
        }
    
    def ensure_directory(self):
        """Ensure download directory exists"""
        os.makedirs(self.download_dir, exist_ok=True)
    
    def extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from TikTok URL"""
        try:
            # Handle different URL formats
            
            # Format 1: https://www.tiktok.com/@username/video/1234567890123456789
            if "/video/" in video_url:
                parts = video_url.split("/video/")
                if len(parts) > 1:
                    video_id = parts[1].split("?")[0]
                    return video_id
            
            # Format 2: https://vt.tiktok.com/ABC123/
            elif "vt.tiktok.com" in video_url or "vm.tiktok.com" in video_url:
                # Follow redirect to get actual video URL
                try:
                    response = requests.head(video_url, allow_redirects=True, timeout=10)
                    final_url = response.url
                    return self.extract_video_id(final_url)
                except:
                    pass
            
            # Format 3: API-style URL
            parsed = urlparse(video_url)
            query_params = parse_qs(parsed.query)
            
            if 'video_id' in query_params:
                return query_params['video_id'][0]
            elif 'id' in query_params:
                return query_params['id'][0]
            
            # Try to extract from path
            path_parts = parsed.path.split('/')
            for part in path_parts:
                if part.isdigit() and len(part) > 15:
                    return part
        
        except Exception as e:
            logger.error(f"Error extracting video ID: {e}")
        
        return None
    
    def get_video_info(self, video_url: str) -> Optional[Dict]:
        """Get video information from TikTok"""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error("Could not extract video ID")
                return None
            
            # API request for video info
            api_url = self.api_endpoints['video_info']
            
            params = {
                'itemId': video_id,
                'language': 'en',
                'region': 'US'
            }
            
            response = requests.get(
                api_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('statusCode') == 0:
                    item_info = data.get('itemInfo', {}).get('itemStruct', {})
                    
                    video_info = {
                        'video_id': video_id,
                        'description': item_info.get('desc', ''),
                        'create_time': item_info.get('createTime', 0),
                        'author': item_info.get('author', {}).get('uniqueId', ''),
                        'author_nickname': item_info.get('author', {}).get('nickname', ''),
                        'music': item_info.get('music', {}).get('title', ''),
                        'stats': item_info.get('stats', {}),
                        'video_url': video_url,
                        'duration': item_info.get('video', {}).get('duration', 0),
                        'width': item_info.get('video', {}).get('width', 0),
                        'height': item_info.get('video', {}).get('height', 0),
                        'cover_url': item_info.get('video', {}).get('cover', ''),
                        'dynamic_cover': item_info.get('video', {}).get('dynamicCover', '')
                    }
                    
                    logger.info(f"Retrieved info for video {video_id}")
                    return video_info
            
            logger.warning(f"API returned status {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    def get_video_download_url(self, video_url: str) -> Optional[str]:
        """Get direct download URL for TikTok video"""
        try:
            video_info = self.get_video_info(video_url)
            if not video_info:
                return None
            
            video_id = video_info['video_id']
            
            # Try multiple methods to get download URL
            
            # Method 1: TikTok API
            try:
                api_url = self.api_endpoints['video_url']
                params = {'itemId': video_id}
                
                response = requests.get(
                    api_url,
                    params=params,
                    headers=self.headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('statusCode') == 0:
                        download_url = data.get('itemInfo', {}).get('video', {}).get('urls', [])
                        if download_url:
                            return download_url[0]
            except:
                pass
            
            # Method 2: Extract from page source
            try:
                response = requests.get(video_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    html = response.text
                    
                    # Look for video URLs in HTML
                    video_patterns = [
                        r'"downloadAddr":"(https://[^"]+)"',
                        r'"playAddr":"(https://[^"]+)"',
                        r'"videoUrl":"(https://[^"]+)"',
                        r'src="(https://[^"]+\.mp4[^"]*)"',
                        r'content="(https://[^"]+\.mp4[^"]*)"'
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, html)
                        for match in matches:
                            # Clean URL
                            clean_url = match.replace('\\u002F', '/')
                            if 'tiktok' in clean_url and '.mp4' in clean_url:
                                return clean_url
            except:
                pass
            
            # Method 3: Third-party API
            try:
                # Using ssstik.io API
                ssstik_url = "https://ssstik.io/abc"
                payload = {
                    'id': video_url,
                    'locale': 'en',
                    'tt': 'YOUR_TOKEN_HERE'  # Would need actual token
                }
                
                response = requests.post(ssstik_url, data=payload, timeout=15)
                if response.status_code == 200:
                    # Parse response for download link
                    # This varies by service
                    pass
            except:
                pass
            
            logger.warning("Could not get download URL")
            return None
            
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return None
    
    def download_video(self, video_url: str, filename: str = None) -> Tuple[bool, Dict]:
        """
        Download TikTok video
        
        Returns:
            Tuple of (success: bool, details: Dict)
        """
        details = {
            'success': False,
            'video_url': video_url,
            'filename': '',
            'filepath': '',
            'file_size': 0,
            'download_time': 0,
            'error': ''
        }
        
        try:
            start_time = time.time()
            
            # Get download URL
            download_url = self.get_video_download_url(video_url)
            if not download_url:
                details['error'] = 'Could not get download URL'
                return False, details
            
            # Generate filename if not provided
            if filename is None:
                video_id = self.extract_video_id(video_url) or 'unknown'
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tiktok_{video_id}_{timestamp}.mp4"
            
            filepath = os.path.join(self.download_dir, filename)
            
            logger.info(f"Downloading video to: {filepath}")
            
            # Download video with progress
            response = requests.get(
                download_url,
                headers=self.headers,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                details['error'] = f"HTTP {response.status_code}"
                return False, details
            
            # Save video
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (1024 * 1024) == 0:
                            percent = (downloaded_size / total_size) * 100
                            logger.debug(f"Download progress: {percent:.1f}%")
            
            # Verify download
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                
                details.update({
                    'success': True,
                    'filename': filename,
                    'filepath': filepath,
                    'file_size': file_size,
                    'download_time': time.time() - start_time,
                    'download_url': download_url
                })
                
                logger.info(f"✅ Video downloaded: {filename} ({file_size:,} bytes, "
                          f"{details['download_time']:.1f}s)")
                
                return True, details
            else:
                details['error'] = 'File not created'
                return False, details
            
        except requests.exceptions.Timeout:
            details['error'] = 'Download timeout'
            logger.error("Download timeout")
            return False, details
            
        except requests.exceptions.RequestException as e:
            details['error'] = str(e)
            logger.error(f"Download error: {e}")
            return False, details
            
        except Exception as e:
            details['error'] = str(e)
            logger.error(f"Unexpected download error: {e}")
            return False, details
    
    def download_video_with_info(self, video_url: str) -> Tuple[bool, Dict]:
        """Download video with full information"""
        try:
            # Get video info first
            video_info = self.get_video_info(video_url)
            if not video_info:
                return False, {'error': 'Could not get video info'}
            
            # Generate filename from info
            author = video_info.get('author', 'unknown').replace('@', '')
            timestamp = datetime.fromtimestamp(video_info.get('create_time', time.time()))
            date_str = timestamp.strftime("%Y%m%d")
            
            filename = f"{author}_{date_str}_{video_info['video_id']}.mp4"
            
            # Download video
            success, download_details = self.download_video(video_url, filename)
            
            if success:
                # Merge info with download details
                result = {**video_info, **download_details}
                return True, result
            else:
                return False, download_details
            
        except Exception as e:
            logger.error(f"Error downloading video with info: {e}")
            return False, {'error': str(e)}
    
    def batch_download(self, video_urls: List[str], max_workers: int = 3) -> List[Dict]:
        """Download multiple videos"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        
        logger.info(f"Starting batch download of {len(video_urls)} videos")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for url in video_urls:
                future = executor.submit(self.download_video_with_info, url)
                futures[future] = url
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    success, details = future.result(timeout=120)  # 2 minute timeout
                    results.append({
                        'url': url,
                        'success': success,
                        'details': details
                    })
                    
                    if success:
                        logger.info(f"✅ Downloaded: {url}")
                    else:
                        logger.warning(f"❌ Failed: {url} - {details.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Error downloading {url}: {e}")
                    results.append({
                        'url': url,
                        'success': False,
                        'error': str(e)
                    })
        
        # Calculate statistics
        successful = sum(1 for r in results if r['success'])
        total_size = sum(r['details'].get('file_size', 0) for r in results if r['success'])
        
        stats = {
            'total_videos': len(results),
            'successful_downloads': successful,
            'success_rate': successful / len(results) if results else 0,
            'total_size_mb': total_size / (1024 * 1024),
            'avg_size_mb': (total_size / successful) / (1024 * 1024) if successful > 0 else 0
        }
        
        logger.info(f"Batch download complete: {stats['success_rate']:.1%} success rate")
        
        return results, stats
    
    def cleanup_old_videos(self, max_age_days: int = 7):
        """Cleanup old downloaded videos"""
        try:
            current_time = time.time()
            removed_count = 0
            total_freed = 0
            
            for filename in os.listdir(self.download_dir):
                if filename.endswith('.mp4'):
                    filepath = os.path.join(self.download_dir, filename)
                    
                    # Get file age
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    # Delete if older than threshold
                    if file_age > (max_age_days * 24 * 3600):
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        
                        removed_count += 1
                        total_freed += file_size
                        
                        logger.debug(f"Removed old video: {filename}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old videos, "
                          f"freed {total_freed / (1024*1024):.1f} MB")
                
        except Exception as e:
            logger.error(f"Error cleaning up old videos: {e}")
    
    def get_video_stats(self, filepath: str) -> Optional[Dict]:
        """Get statistics about downloaded video"""
        try:
            if not os.path.exists(filepath):
                return None
            
            import subprocess
            
            # Use ffprobe if available
            try:
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height,duration,bit_rate,codec_name',
                    '-of', 'json',
                    filepath
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    
                    if 'streams' in probe_data and len(probe_data['streams']) > 0:
                        stream = probe_data['streams'][0]
                        
                        stats = {
                            'width': int(stream.get('width', 0)),
                            'height': int(stream.get('height', 0)),
                            'duration': float(stream.get('duration', 0)),
                            'bitrate': int(stream.get('bit_rate', 0)),
                            'codec': stream.get('codec_name', 'unknown'),
                            'file_size': os.path.getsize(filepath),
                            'created': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                        }
                        
                        return stats
            except:
                pass
            
            # Fallback: basic file info
            stats = {
                'file_size': os.path.getsize(filepath),
                'created': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                'extension': os.path.splitext(filepath)[1]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting video stats: {e}")
            return None
    
    def create_video_library(self) -> List[Dict]:
        """Create library of all downloaded videos"""
        library = []
        
        try:
            for filename in os.listdir(self.download_dir):
                if filename.endswith('.mp4'):
                    filepath = os.path.join(self.download_dir, filename)
                    
                    # Get basic info
                    video_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'file_size': os.path.getsize(filepath),
                        'created': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                        'stats': self.get_video_stats(filepath)
                    }
                    
                    # Try to extract info from filename
                    if '_' in filename:
                        parts = filename.split('_')
                        if len(parts) >= 3:
                            video_info['author'] = parts[0]
                            video_info['date'] = parts[1]
                            video_info['video_id'] = parts[2].replace('.mp4', '')
                    
                    library.append(video_info)
            
            # Sort by creation date (newest first)
            library.sort(key=lambda x: x['created'], reverse=True)
            
            logger.info(f"Video library created with {len(library)} videos")
            return library
            
        except Exception as e:
            logger.error(f"Error creating video library: {e}")
            return []