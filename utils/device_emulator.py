"""
Device Emulator - Emulate different devices for TikTok
"""

import random
import json
from typing import Dict, List
from fake_useragent import UserAgent

class DeviceEmulator:
    def __init__(self):
        self.devices = self.load_device_profiles()
        self.ua = UserAgent()
    
    def load_device_profiles(self) -> Dict:
        """Load device profiles"""
        return {
            "android": [
                {
                    "name": "Samsung Galaxy S21",
                    "user_agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "screen": "1080x2400",
                    "platform": "Android",
                    "version": "11"
                },
                {
                    "name": "Google Pixel 6",
                    "user_agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "screen": "1080x2400",
                    "platform": "Android",
                    "version": "12"
                },
                {
                    "name": "Xiaomi Redmi Note 10",
                    "user_agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                    "screen": "1080x2400",
                    "platform": "Android",
                    "version": "11"
                }
            ],
            "ios": [
                {
                    "name": "iPhone 13",
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                    "screen": "1170x2532",
                    "platform": "iOS",
                    "version": "15.0"
                },
                {
                    "name": "iPad Air",
                    "user_agent": "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                    "screen": "1640x2360",
                    "platform": "iOS",
                    "version": "15.0"
                }
            ],
            "desktop": [
                {
                    "name": "Windows Chrome",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "screen": "1920x1080",
                    "platform": "Windows",
                    "version": "10"
                },
                {
                    "name": "Mac Safari",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                    "screen": "2560x1600",
                    "platform": "macOS",
                    "version": "10.15"
                }
            ]
        }
    
    def get_random_device(self, device_type: str = "random") -> Dict:
        """Get random device profile"""
        if device_type == "random":
            device_type = random.choice(list(self.devices.keys()))
        
        if device_type in self.devices:
            return random.choice(self.devices[device_type])
        
        # Fallback to random user agent
        return {
            "name": "Random Device",
            "user_agent": self.ua.random,
            "screen": "1920x1080",
            "platform": "Unknown",
            "version": "Unknown"
        }
    
    def get_device_headers(self, device: Dict) -> Dict:
        """Get headers for specific device"""
        headers = {
            "User-Agent": device["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }
        
        # Add device-specific headers
        if device["platform"].lower() == "android":
            headers["X-Requested-With"] = "com.zhiliaoapp.musically"
        elif device["platform"].lower() == "ios":
            headers["X-Requested-With"] = "TikTok"
        
        return headers
    
    def get_viewport_size(self, device: Dict) -> tuple:
        """Get viewport size from device"""
        if "screen" in device:
            try:
                width, height = map(int, device["screen"].split("x"))
                return (width, height)
            except:
                pass
        
        return (1920, 1080)  # Default
    
    def emulate_device(self, driver, device: Dict):
        """Emulate device in WebDriver"""
        # Set user agent
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": device["user_agent"]}
        )
        
        # Set viewport size
        width, height = self.get_viewport_size(device)
        driver.set_window_size(width, height)
        
        # Emulate device metrics
        device_metrics = {
            "width": width,
            "height": height,
            "deviceScaleFactor": random.choice([1, 2, 3]),
            "mobile": device["platform"].lower() in ["android", "ios"]
        }
        
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", device_metrics)
        
        # Set geolocation (optional)
        if random.random() < 0.5:
            location = self.get_random_location()
            driver.execute_cdp_cmd(
                "Emulation.setGeolocationOverride",
                location
            )
    
    def get_random_location(self) -> Dict:
        """Get random location coordinates"""
        locations = [
            {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 100},  # New York
            {"latitude": 34.0522, "longitude": -118.2437, "accuracy": 100},  # LA
            {"latitude": 51.5074, "longitude": -0.1278, "accuracy": 100},  # London
            {"latitude": 35.6762, "longitude": 139.6503, "accuracy": 100},  # Tokyo
            {"latitude": 48.8566, "longitude": 2.3522, "accuracy": 100},  # Paris
        ]
        
        return random.choice(locations)
    
    def get_fingerprint(self, device: Dict) -> Dict:
        """Generate device fingerprint"""
        fingerprint = {
            "userAgent": device["user_agent"],
            "platform": device["platform"],
            "screenResolution": device["screen"],
            "timezone": random.choice(["America/New_York", "Europe/London", "Asia/Tokyo"]),
            "language": random.choice(["en-US", "en-GB", "ja-JP"]),
            "cpuCores": random.choice([4, 6, 8]),
            "memory": random.choice([4, 8, 16]),
            "webglVendor": random.choice(["Google Inc.", "Intel Inc.", "NVIDIA Corporation"]),
            "webglRenderer": random.choice(["ANGLE", "WebKit", "Mozilla"])
        }
        
        return fingerprint