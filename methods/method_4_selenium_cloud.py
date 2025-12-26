"""
Method 4: Selenium Cloud/Grid - Use remote Selenium servers
"""

import json
import time
import random
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class SeleniumCloudMethod:
    def __init__(self):
        self.name = "selenium_cloud"
        self.success_rate = 75  # 75% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Cloud services (free tiers available)
        self.cloud_services = [
            {
                'name': 'BrowserStack',
                'url': 'https://hub.browserstack.com/wd/hub',
                'free': True  # Has free trial
            },
            {
                'name': 'SauceLabs',
                'url': 'https://ondemand.us-west-1.saucelabs.com/wd/hub',
                'free': True  # Has free tier
            },
            {
                'name': 'LambdaTest',
                'url': 'https://hub.lambdatest.com/wd/hub',
                'free': True  # Has free tier
            },
            {
                'name': 'TestingBot',
                'url': 'https://hub.testingbot.com/wd/hub',
                'free': True  # Has free trial
            },
            {
                'name': 'CrossBrowserTesting',
                'url': 'https://hub.crossbrowsertesting.com/wd/hub',
                'free': True  # Has free trial
            }
        ]
        
        # Load credentials
        self.credentials = self.load_credentials()
    
    def load_credentials(self):
        """Load cloud service credentials"""
        try:
            with open('config/cloud_credentials.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("No cloud credentials found, using public grids")
            return {}
    
    def is_available(self) -> bool:
        """Check if cloud services are available"""
        # Check if any cloud service is configured
        if self.credentials:
            return True
        
        # Try public Selenium Grid
        try:
            import requests
            public_grids = [
                'http://localhost:4444/wd/hub',
                'http://selenium-hub:4444/wd/hub'
            ]
            
            for grid_url in public_grids:
                try:
                    response = requests.get(grid_url + '/status', timeout=5)
                    if response.status_code == 200:
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using Selenium Cloud"""
        logger.info(f"Selenium Cloud Method: Sending {view_count} views")
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'cloud_services_used': []
        }
        
        # Determine which cloud service to use
        cloud_service = self.select_cloud_service()
        
        for i in range(view_count):
            try:
                if self.send_cloud_view(video_url, cloud_service):
                    results['success_count'] += 1
                    self.successful_views += 1
                    results['cloud_services_used'].append(cloud_service['name'])
                else:
                    results['failed_count'] += 1
                
                self.total_views_sent += 1
                
                # Rotate cloud service occasionally
                if i % 5 == 0:
                    cloud_service = self.select_cloud_service()
                
                # Random delay
                if i < view_count - 1:
                    time.sleep(random.uniform(3, 8))
                    
            except Exception as e:
                logger.error(f"Error sending cloud view {i+1}: {e}")
                results['failed_count'] += 1
        
        self.last_used = time.time()
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"Selenium Cloud Results: {results['success_count']}/{view_count} successful")
        return results
    
    def select_cloud_service(self) -> Dict:
        """Select a cloud service to use"""
        # First try configured services
        if self.credentials:
            service_name = random.choice(list(self.credentials.keys()))
            service_config = next(
                (s for s in self.cloud_services if s['name'] == service_name),
                self.cloud_services[0]
            )
            
            return {
                'name': service_name,
                'url': service_config['url'],
                'credentials': self.credentials.get(service_name, {})
            }
        
        # Fallback to public grids
        public_grids = [
            'http://localhost:4444/wd/hub',
            'http://selenium-hub:4444/wd/hub',
            'http://grid:4444/wd/hub'
        ]
        
        return {
            'name': 'public_grid',
            'url': random.choice(public_grids),
            'credentials': {}
        }
    
    def send_cloud_view(self, video_url: str, cloud_service: Dict) -> bool:
        """Send a single view using cloud Selenium"""
        driver = None
        try:
            # Setup capabilities
            capabilities = self.get_capabilities(cloud_service['name'])
            
            # Add credentials if available
            if 'credentials' in cloud_service and cloud_service['credentials']:
                creds = cloud_service['credentials']
                if 'username' in creds and 'access_key' in creds:
                    capabilities['browserstack.user'] = creds['username']
                    capabilities['browserstack.key'] = creds['access_key']
            
            # Create remote driver
            driver = webdriver.Remote(
                command_executor=cloud_service['url'],
                desired_capabilities=capabilities
            )
            
            # Navigate to video
            driver.get(video_url)
            time.sleep(5)
            
            # Wait for video
            wait = WebDriverWait(driver, 20)
            video_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            
            # Play video
            driver.execute_script("arguments[0].play();", video_element)
            
            # Watch for random time
            watch_time = random.randint(15, 30)
            logger.debug(f"Watching video for {watch_time} seconds on {cloud_service['name']}")
            
            for _ in range(watch_time):
                # Random interactions
                if random.random() < 0.1:
                    self.random_scroll(driver)
                
                time.sleep(1)
            
            # Random engagement
            if random.random() < 0.2:
                self.simulate_like(driver)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in cloud view ({cloud_service['name']}): {e}")
            return False
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def get_capabilities(self, service_name: str) -> Dict:
        """Get browser capabilities for cloud service"""
        # Common capabilities
        capabilities = {
            'browserName': random.choice(['chrome', 'firefox', 'safari']),
            'version': 'latest',
            'platform': random.choice(['WINDOWS', 'MAC', 'LINUX']),
            'acceptSslCerts': 'true',
            'acceptInsecureCerts': 'true',
            'javascriptEnabled': 'true',
            'timeouts': {'implicit': 30000, 'pageLoad': 300000, 'script': 30000}
        }
        
        # Service-specific capabilities
        if service_name == 'BrowserStack':
            capabilities.update({
                'browserstack.local': 'false',
                'browserstack.debug': 'true',
                'browserstack.console': 'errors',
                'browserstack.networkLogs': 'true',
                'browserstack.video': 'true'
            })
        elif service_name == 'SauceLabs':
            capabilities.update({
                'sauce:options': {
                    'screenResolution': '1920x1080',
                    'timeZone': 'UTC',
                    'maxDuration': 1800,
                    'commandTimeout': 300,
                    'idleTimeout': 90
                }
            })
        elif service_name == 'LambdaTest':
            capabilities.update({
                'LT:Options': {
                    'video': True,
                    'visual': True,
                    'network': True,
                    'console': True
                }
            })
        
        # Randomize browser version
        chrome_versions = ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '111', '112', '113', '114', '115', '116', '117', '118', '119', '120']
        firefox_versions = ['90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '110', '111', '112', '113', '114', '115']
        
        if capabilities['browserName'] == 'chrome':
            capabilities['version'] = random.choice(chrome_versions)
        elif capabilities['browserName'] == 'firefox':
            capabilities['version'] = random.choice(firefox_versions)
        
        return capabilities
    
    def random_scroll(self, driver):
        """Random scroll action"""
        try:
            scroll_amount = random.choice([-200, -100, 100, 200, 300])
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
        except:
            pass
    
    def simulate_like(self, driver):
        """Simulate liking the video"""
        try:
            like_buttons = driver.find_elements(
                By.CSS_SELECTOR,
                '[data-e2e="like-icon"], button[aria-label*="Like"], svg[aria-label*="Like"]'
            )
            
            for button in like_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(random.uniform(0.5, 1.5))
                        break
                except:
                    continue
        except:
            pass
    
    def setup_public_grid(self):
        """Setup instructions for public Selenium Grid"""
        instructions = """
        To use public Selenium Grid:
        
        1. Install Docker
        2. Run Selenium Grid:
           docker run -d -p 4444:4444 --name selenium-hub selenium/hub:latest
        3. Run Chrome nodes:
           docker run -d --link selenium-hub:hub selenium/node-chrome:latest
        4. Run Firefox nodes:
           docker run -d --link selenium-hub:hub selenium/node-firefox:latest
        
        Or use free cloud services:
        1. Sign up for BrowserStack (free trial)
        2. Sign up for SauceLabs (free tier)
        3. Sign up for LambdaTest (free tier)
        
        Add credentials to config/cloud_credentials.json
        """
        
        logger.info(instructions)
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup method"""
        pass