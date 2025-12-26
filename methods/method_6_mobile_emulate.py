"""
Method 6: Mobile Device Emulation - Emulate mobile browsers
"""

import time
import random
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class MobileEmulationMethod:
    def __init__(self):
        self.name = "mobile_emulation"
        self.success_rate = 90  # 90% success rate (mobile is more trusted)
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Mobile device profiles
        self.mobile_devices = [
            # iPhone devices
            {
                "name": "iPhone 13",
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "width": 390,
                "height": 844,
                "pixelRatio": 3,
                "touch": True
            },
            {
                "name": "iPhone 12 Pro",
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
                "width": 390,
                "height": 844,
                "pixelRatio": 3,
                "touch": True
            },
            {
                "name": "iPhone SE",
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
                "width": 375,
                "height": 667,
                "pixelRatio": 2,
                "touch": True
            },
            
            # Android devices
            {
                "name": "Samsung Galaxy S21",
                "userAgent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "width": 360,
                "height": 800,
                "pixelRatio": 4,
                "touch": True
            },
            {
                "name": "Google Pixel 6",
                "userAgent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "width": 412,
                "height": 915,
                "pixelRatio": 3.5,
                "touch": True
            },
            {
                "name": "Xiaomi Redmi Note 10",
                "userAgent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "width": 393,
                "height": 851,
                "pixelRatio": 2.75,
                "touch": True
            },
            
            # iPad devices
            {
                "name": "iPad Air",
                "userAgent": "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "width": 820,
                "height": 1180,
                "pixelRatio": 2,
                "touch": True
            },
            {
                "name": "iPad Pro",
                "userAgent": "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "width": 1024,
                "height": 1366,
                "pixelRatio": 2,
                "touch": True
            }
        ]
    
    def is_available(self) -> bool:
        """Check if mobile emulation is available"""
        return True  # Always available with Chrome
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using mobile emulation"""
        logger.info(f"Mobile Emulation Method: Sending {view_count} views")
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'devices_used': []
        }
        
        for i in range(view_count):
            try:
                # Select random mobile device
                device = random.choice(self.mobile_devices)
                
                if self.send_mobile_view(video_url, device):
                    results['success_count'] += 1
                    self.successful_views += 1
                    results['devices_used'].append(device['name'])
                else:
                    results['failed_count'] += 1
                
                self.total_views_sent += 1
                
                # Random delay between views
                if i < view_count - 1:
                    time.sleep(random.uniform(3, 7))
                    
            except Exception as e:
                logger.error(f"Error sending mobile view {i+1}: {e}")
                results['failed_count'] += 1
        
        self.last_used = time.time()
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"Mobile Emulation Results: {results['success_count']}/{view_count} successful")
        return results
    
    def send_mobile_view(self, video_url: str, device: Dict) -> bool:
        """Send a single view with mobile emulation"""
        driver = None
        try:
            # Setup Chrome with mobile emulation
            options = uc.ChromeOptions()
            
            # Mobile-specific arguments
            mobile_args = [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                f'--window-size={device["width"]},{device["height"]}',
                '--use-mobile-user-agent'
            ]
            
            for arg in mobile_args:
                options.add_argument(arg)
            
            # Enable mobile emulation
            mobile_emulation = {
                "deviceMetrics": {
                    "width": device["width"],
                    "height": device["height"],
                    "pixelRatio": device["pixelRatio"]
                },
                "userAgent": device["userAgent"]
            }
            
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # Create driver
            driver = uc.Chrome(options=options, use_subprocess=True)
            
            # Set additional mobile capabilities
            driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {
                'enabled': device.get('touch', True)
            })
            
            # Set geolocation (optional)
            if random.random() < 0.3:
                location = self.get_random_location()
                driver.execute_cdp_cmd('Emulation.setGeolocationOverride', location)
            
            # Navigate to video
            driver.get(video_url)
            
            # Wait for page load
            wait = WebDriverWait(driver, 20)
            
            # Wait for video element
            video_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Simulate mobile touch interactions
            self.simulate_mobile_interactions(driver)
            
            # Watch video
            watch_time = random.randint(15, 45)
            logger.debug(f"Watching video on {device['name']} for {watch_time} seconds")
            
            for _ in range(watch_time):
                # Random mobile interactions
                if random.random() < 0.1:
                    self.simulate_touch_scroll(driver)
                if random.random() < 0.05:
                    self.simulate_touch_swipe(driver)
                
                time.sleep(1)
            
            # Random engagement (more likely on mobile)
            if random.random() < 0.4:  # 40% chance to like on mobile
                self.simulate_mobile_like(driver)
            
            if random.random() < 0.2:  # 20% chance to comment
                self.simulate_mobile_comment(driver)
            
            if random.random() < 0.3:  # 30% chance to share
                self.simulate_mobile_share(driver)
            
            # Watch a bit more
            time.sleep(random.randint(3, 10))
            
            return True
            
        except Exception as e:
            logger.error(f"Error in mobile view ({device['name']}): {e}")
            return False
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def simulate_mobile_interactions(self, driver):
        """Simulate mobile-specific interactions"""
        try:
            # Touch scroll
            for _ in range(random.randint(2, 4)):
                scroll_y = random.randint(100, 300)
                driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Simulate touch events
            touch_script = """
            // Simulate touch start
            const touchStart = new Touch({
                identifier: Date.now(),
                target: document.body,
                clientX: 100,
                clientY: 200,
                screenX: 100,
                screenY: 200,
                pageX: 100,
                pageY: 200,
                radiusX: 5,
                radiusY: 5,
                rotationAngle: 0,
                force: 1
            });
            
            const touchEvent = new TouchEvent('touchstart', {
                touches: [touchStart],
                targetTouches: [touchStart],
                changedTouches: [touchStart],
                bubbles: true
            });
            
            document.body.dispatchEvent(touchEvent);
            """
            
            driver.execute_script(touch_script)
            time.sleep(random.uniform(0.1, 0.5))
            
        except:
            pass
    
    def simulate_touch_scroll(self, driver):
        """Simulate touch scrolling"""
        try:
            scroll_amount = random.randint(100, 400)
            driver.execute_script(f"""
            // Smooth scroll for mobile
            window.scrollTo({{
                top: window.scrollY + {scroll_amount},
                behavior: 'smooth'
            }});
            """)
            time.sleep(random.uniform(0.5, 1.5))
        except:
            pass
    
    def simulate_touch_swipe(self, driver):
        """Simulate touch swipe"""
        try:
            # Simulate swipe gesture
            swipe_script = """
            // Simulate swipe
            const startX = 200;
            const startY = 400;
            const endX = 200;
            const endY = 200;
            
            // Touch start
            const touchStart = new Touch({
                identifier: 1,
                target: document.body,
                clientX: startX,
                clientY: startY,
                screenX: startX,
                screenY: startY,
                pageX: startX,
                pageY: startY
            });
            
            const touchStartEvent = new TouchEvent('touchstart', {
                touches: [touchStart],
                targetTouches: [touchStart],
                changedTouches: [touchStart]
            });
            
            document.body.dispatchEvent(touchStartEvent);
            
            // Touch move
            const touchMove = new Touch({
                identifier: 1,
                target: document.body,
                clientX: endX,
                clientY: endY,
                screenX: endX,
                screenY: endY,
                pageX: endX,
                pageY: endY
            });
            
            const touchMoveEvent = new TouchEvent('touchmove', {
                touches: [touchMove],
                targetTouches: [touchMove],
                changedTouches: [touchMove]
            });
            
            document.body.dispatchEvent(touchMoveEvent);
            
            // Touch end
            const touchEndEvent = new TouchEvent('touchend', {
                touches: [],
                targetTouches: [],
                changedTouches: [touchMove]
            });
            
            document.body.dispatchEvent(touchEndEvent);
            """
            
            driver.execute_script(swipe_script)
            time.sleep(random.uniform(0.5, 1))
            
        except:
            pass
    
    def simulate_mobile_like(self, driver):
        """Simulate like on mobile"""
        try:
            # Try different mobile like button selectors
            like_selectors = [
                '[data-e2e="like-icon"]',
                'svg[aria-label*="Like"]',
                'path[d*="M12.525"]',  # TikTok like icon path
                'button:has(svg)'
            ]
            
            for selector in like_selectors:
                like_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in like_buttons:
                    try:
                        if button.is_displayed():
                            # Simulate touch tap
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(random.uniform(0.5, 1.5))
                            logger.debug("Liked video on mobile")
                            return
                    except:
                        continue
        except:
            pass
    
    def simulate_mobile_comment(self, driver):
        """Simulate comment on mobile"""
        try:
            # Find comment button/input
            comment_elements = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-e2e="comment-icon"], [aria-label*="Comment"], textarea'
            )
            
            for element in comment_elements:
                try:
                    if element.is_displayed():
                        # Tap to focus
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(random.uniform(0.5, 1))
                        
                        # Type random comment
                        comments = [
                            "Nice video! 👍",
                            "Love this! ❤️",
                            "Great content!",
                            "Awesome! 🔥",
                            "So good!",
                            "Watched! 👀",
                            "Interesting!",
                            "Keep it up! 💪"
                        ]
                        
                        comment = random.choice(comments)
                        element.send_keys(comment)
                        time.sleep(random.uniform(1, 2))
                        
                        # Find send button
                        send_buttons = driver.find_elements(
                            By.CSS_SELECTOR,
                            'button[type="submit"], button:has(svg)'
                        )
                        
                        for btn in send_buttons:
                            if btn.is_displayed():
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(random.uniform(1, 2))
                                logger.debug("Commented on mobile")
                                break
                        
                        break
                except:
                    continue
        except:
            pass
    
    def simulate_mobile_share(self, driver):
        """Simulate share on mobile"""
        try:
            share_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-e2e="share-icon"], [aria-label*="Share"]'
            )
            
            for button in share_buttons:
                try:
                    if button.is_displayed():
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(random.uniform(1, 2))
                        
                        # Close share sheet (common on mobile)
                        driver.find_element(By.TAG_NAME, 'body').send_keys('ESC')
                        time.sleep(random.uniform(0.5, 1))
                        logger.debug("Shared on mobile")
                        break
                except:
                    continue
        except:
            pass
    
    def get_random_location(self):
        """Get random location for mobile"""
        locations = [
            {"latitude": 40.7128, "longitude": -74.0060, "accuracy": 50},  # NYC
            {"latitude": 34.0522, "longitude": -118.2437, "accuracy": 50},  # LA
            {"latitude": 51.5074, "longitude": -0.1278, "accuracy": 50},   # London
            {"latitude": 35.6762, "longitude": 139.6503, "accuracy": 50},  # Tokyo
            {"latitude": 48.8566, "longitude": 2.3522, "accuracy": 50},    # Paris
            {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 50}, # SF
            {"latitude": 55.7558, "longitude": 37.6173, "accuracy": 50},   # Moscow
            {"latitude": -33.8688, "longitude": 151.2093, "accuracy": 50}, # Sydney
        ]
        
        return random.choice(locations)
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup method"""
        pass