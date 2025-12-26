"""
Method 1: Browser Automation with Human-like Behavior
Most reliable method for real views
"""

import time
import random
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class BrowserMethod:
    def __init__(self):
        self.name = "browser_human"
        self.success_rate = 85  # 85% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        self.drivers = []
        self.max_drivers = 5
        
    def is_available(self) -> bool:
        """Check if method is available"""
        try:
            # Test Chrome availability
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(options=options)
            driver.quit()
            return True
        except:
            return False
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using browser automation"""
        logger.info(f"Browser Method: Sending {view_count} views to {video_url}")
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'details': []
        }
        
        for i in range(view_count):
            try:
                if self.send_single_view(video_url):
                    results['success_count'] += 1
                    self.successful_views += 1
                else:
                    results['failed_count'] += 1
                
                self.total_views_sent += 1
                
                # Random delay between views
                if i < view_count - 1:
                    time.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                logger.error(f"Error sending view {i+1}: {e}")
                results['failed_count'] += 1
        
        self.last_used = time.time()
        
        # Calculate success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"Browser Method Results: {results['success_count']}/{view_count} successful")
        return results
    
    def send_single_view(self, video_url: str) -> bool:
        """Send a single view with human-like behavior"""
        driver = None
        try:
            # Setup undetected Chrome
            options = uc.ChromeOptions()
            
            # Random user agent
            ua = UserAgent()
            user_agent = ua.random
            options.add_argument(f'user-agent={user_agent}')
            
            # Anti-detection arguments
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Headless or normal
            if random.choice([True, False]):
                options.add_argument('--headless=new')
            
            # Create driver
            driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=120  # Use Chrome 120
            )
            
            # Set window size
            driver.set_window_size(
                random.randint(1200, 1920),
                random.randint(800, 1080)
            )
            
            # Navigate to video
            driver.get(video_url)
            
            # Wait for page load
            wait = WebDriverWait(driver, 20)
            
            # Wait for video element
            video_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Simulate human behavior
            self.simulate_human_behavior(driver)
            
            # Watch video
            watch_time = random.randint(15, 45)  # 15-45 seconds
            logger.debug(f"Watching video for {watch_time} seconds")
            
            for _ in range(watch_time):
                # Random interactions during watch
                if random.random() < 0.1:  # 10% chance
                    self.random_scroll(driver)
                if random.random() < 0.05:  # 5% chance
                    self.random_mouse_move(driver)
                
                time.sleep(1)
            
            # Random engagement
            if random.random() < 0.3:  # 30% chance to like
                self.simulate_like(driver)
            
            if random.random() < 0.1:  # 10% chance to comment
                self.simulate_comment(driver)
            
            if random.random() < 0.2:  # 20% chance to share
                self.simulate_share(driver)
            
            # Scroll through comments
            if random.random() < 0.4:
                self.scroll_comments(driver)
            
            # Watch a bit more
            time.sleep(random.randint(3, 10))
            
            return True
            
        except Exception as e:
            logger.error(f"Error in single view: {e}")
            return False
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def simulate_human_behavior(self, driver):
        """Simulate human-like browsing behavior"""
        actions = ActionChains(driver)
        
        # Random mouse movements
        for _ in range(random.randint(3, 8)):
            x_offset = random.randint(-100, 100)
            y_offset = random.randint(-100, 100)
            actions.move_by_offset(x_offset, y_offset)
            actions.perform()
            time.sleep(random.uniform(0.1, 0.5))
        
        # Random scrolls
        for _ in range(random.randint(2, 5)):
            scroll_amount = random.randint(100, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
    
    def random_scroll(self, driver):
        """Random scroll action"""
        scroll_amount = random.choice([-300, -200, -100, 100, 200, 300])
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(0.5, 1))
    
    def random_mouse_move(self, driver):
        """Random mouse movement"""
        actions = ActionChains(driver)
        actions.move_by_offset(
            random.randint(-50, 50),
            random.randint(-50, 50)
        ).perform()
        time.sleep(random.uniform(0.1, 0.3))
    
    def simulate_like(self, driver):
        """Simulate liking the video"""
        try:
            # Find like button
            like_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-e2e="like-icon"], [aria-label*="Like"], button:has(svg)'
            )
            
            for button in like_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(random.uniform(0.5, 1.5))
                        logger.debug("Liked the video")
                        break
                except:
                    continue
        except:
            pass
    
    def simulate_comment(self, driver):
        """Simulate commenting"""
        try:
            # Find comment box
            comment_boxes = driver.find_elements(
                By.CSS_SELECTOR,
                'textarea, [contenteditable="true"], [data-e2e="comment-input"]'
            )
            
            for box in comment_boxes:
                try:
                    if box.is_displayed():
                        box.click()
                        time.sleep(random.uniform(0.5, 1))
                        
                        # Type random comment
                        comments = [
                            "Nice! 👍",
                            "Great video!",
                            "Love this! ❤️",
                            "Awesome content!",
                            "🔥🔥🔥",
                            "So good!",
                            "Watched till end!",
                            "Interesting!",
                            "Keep it up!",
                            "Good one!"
                        ]
                        
                        comment = random.choice(comments)
                        box.send_keys(comment)
                        time.sleep(random.uniform(1, 2))
                        
                        # Find submit button
                        submit_buttons = driver.find_elements(
                            By.CSS_SELECTOR,
                            'button[type="submit"], button:has(svg)'
                        )
                        
                        for btn in submit_buttons:
                            if btn.is_displayed() and btn.text in ["Post", "Comment", "Send"]:
                                btn.click()
                                time.sleep(random.uniform(1, 2))
                                logger.debug("Commented on video")
                                break
                        
                        break
                except:
                    continue
        except:
            pass
    
    def simulate_share(self, driver):
        """Simulate sharing"""
        try:
            share_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-e2e="share-icon"], [aria-label*="Share"], button:has(svg)'
            )
            
            for button in share_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(random.uniform(1, 2))
                        
                        # Close share modal
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(random.uniform(0.5, 1))
                        logger.debug("Shared video")
                        break
                except:
                    continue
        except:
            pass
    
    def scroll_comments(self, driver):
        """Scroll through comments"""
        try:
            # Find comments section
            comments_section = driver.find_element(
                By.CSS_SELECTOR,
                '[data-e2e="comment-list"], .comment-list, div[class*="comment"]'
            )
            
            # Scroll within comments
            for _ in range(random.randint(3, 8)):
                driver.execute_script(
                    "arguments[0].scrollTop += 200;",
                    comments_section
                )
                time.sleep(random.uniform(0.5, 1))
        except:
            pass
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup all drivers"""
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.drivers = []
        logger.info("Browser method cleanup completed")