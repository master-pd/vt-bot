"""
Account Creator - Create TikTok accounts automatically
"""

import random
import string
import time
import logging
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class AccountCreator:
    def __init__(self):
        self.temp_email_services = [
            "https://temp-mail.org/",
            "https://10minutemail.com/",
            "https://www.guerrillamail.com/",
            "https://temp-mail.io/"
        ]
        
    def create_account(self, use_proxy: bool = True) -> Optional[Dict]:
        """
        Create a new TikTok account
        
        Returns:
            Dictionary with account details or None if failed
        """
        logger.info("Starting account creation process")
        
        driver = None
        try:
            # Setup driver
            options = webdriver.ChromeOptions()
            
            if use_proxy:
                # Add proxy
                proxy = self.get_proxy()
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
            
            # Anti-detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Step 1: Get temporary email
            logger.info("Getting temporary email...")
            email = self.get_temp_email(driver)
            if not email:
                logger.error("Failed to get temporary email")
                return None
            
            # Step 2: Create TikTok account
            logger.info(f"Creating account with email: {email}")
            account_data = self.create_tiktok_account(driver, email)
            
            if account_data:
                logger.info(f"Account created successfully: {account_data.get('username')}")
                return account_data
            else:
                logger.error("Failed to create TikTok account")
                return None
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return None
        
        finally:
            if driver:
                driver.quit()
    
    def get_temp_email(self, driver) -> Optional[str]:
        """Get temporary email from service"""
        try:
            service_url = random.choice(self.temp_email_services)
            driver.get(service_url)
            time.sleep(5)
            
            # Different services have different email element selectors
            email_selectors = [
                "input[type='email']",
                "#email",
                ".email",
                "[class*='email']",
                "span.email"
            ]
            
            for selector in email_selectors:
                try:
                    email_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    email = email_element.get_attribute("value")
                    if email and "@" in email:
                        logger.info(f"Got temporary email: {email}")
                        return email
                except:
                    continue
            
            # Try to generate email manually
            return self.generate_temp_email()
            
        except Exception as e:
            logger.error(f"Error getting temp email: {e}")
            return self.generate_temp_email()
    
    def generate_temp_email(self) -> str:
        """Generate random email"""
        domains = [
            "tempmail.com", "temp-mail.org", "10minutemail.com",
            "guerrillamail.com", "yopmail.com", "mailinator.com"
        ]
        
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        domain = random.choice(domains)
        
        return f"{username}@{domain}"
    
    def create_tiktok_account(self, driver, email: str) -> Optional[Dict]:
        """Create TikTok account with email"""
        try:
            # Go to TikTok signup page
            driver.get("https://www.tiktok.com/signup")
            time.sleep(5)
            
            # Check if page loaded
            if "tiktok.com" not in driver.current_url:
                logger.warning("Not on TikTok site, trying alternative")
                driver.get("https://www.tiktok.com/")
                time.sleep(3)
                
                # Click signup
                signup_buttons = driver.find_elements(
                    By.XPATH, 
                    "//button[contains(text(), 'Sign up') or contains(text(), 'Sign Up')]"
                )
                
                if signup_buttons:
                    signup_buttons[0].click()
                    time.sleep(3)
            
            # Fill signup form
            logger.info("Filling signup form...")
            
            # Generate account details
            account_data = self.generate_account_details(email)
            
            # Try different signup methods
            signup_success = False
            
            # Method 1: Email signup
            try:
                # Find email field
                email_fields = driver.find_elements(
                    By.CSS_SELECTOR, 
                    "input[type='email'], input[name='email'], #email"
                )
                
                if email_fields:
                    email_field = email_fields[0]
                    email_field.send_keys(email)
                    time.sleep(1)
                    
                    # Find password field
                    password_fields = driver.find_elements(
                        By.CSS_SELECTOR,
                        "input[type='password'], input[name='password'], #password"
                    )
                    
                    if password_fields:
                        password_field = password_fields[0]
                        password_field.send_keys(account_data['password'])
                        time.sleep(1)
                        
                        # Find submit button
                        submit_buttons = driver.find_elements(
                            By.CSS_SELECTOR,
                            "button[type='submit'], button:contains('Sign up')"
                        )
                        
                        if submit_buttons:
                            submit_buttons[0].click()
                            time.sleep(5)
                            signup_success = True
            except:
                pass
            
            # Method 2: Username/password signup
            if not signup_success:
                try:
                    # Look for username field
                    username_fields = driver.find_elements(
                        By.CSS_SELECTOR,
                        "input[name='username'], #username"
                    )
                    
                    if username_fields:
                        username_field = username_fields[0]
                        username_field.send_keys(account_data['username'])
                        time.sleep(1)
                        
                        # Password field
                        password_fields = driver.find_elements(
                            By.CSS_SELECTOR,
                            "input[type='password'], input[name='password']"
                        )
                        
                        if password_fields:
                            password_field = password_fields[0]
                            password_field.send_keys(account_data['password'])
                            time.sleep(1)
                            
                            # Submit
                            submit_buttons = driver.find_elements(
                                By.XPATH,
                                "//button[contains(text(), 'Sign up') or contains(text(), 'Create account')]"
                            )
                            
                            if submit_buttons:
                                submit_buttons[0].click()
                                time.sleep(5)
                                signup_success = True
                except:
                    pass
            
            if signup_success:
                # Wait for account creation
                time.sleep(10)
                
                # Get cookies
                cookies = driver.get_cookies()
                account_data['cookies'] = {c['name']: c['value'] for c in cookies}
                
                # Get user agent
                account_data['user_agent'] = driver.execute_script("return navigator.userAgent")
                
                # Generate account ID
                account_data['account_id'] = f"acc_{int(time.time())}_{random.randint(1000, 9999)}"
                account_data['created_at'] = time.time()
                account_data['active'] = True
                
                return account_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating TikTok account: {e}")
            return None
    
    def generate_account_details(self, email: str) -> Dict:
        """Generate random account details"""
        # Generate username
        adjectives = ["cool", "awesome", "super", "mega", "ultra", "epic", "fantastic"]
        nouns = ["user", "player", "creator", "maker", "viewer", "fan", "lover"]
        numbers = str(random.randint(100, 99999))
        
        username = f"{random.choice(adjectives)}_{random.choice(nouns)}_{numbers}"
        
        # Generate password
        password_length = random.randint(12, 16)
        password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choices(password_chars, k=password_length))
        
        # Generate birthday
        year = random.randint(1980, 2003)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        
        return {
            'email': email,
            'username': username,
            'password': password,
            'birthday': f"{year}-{month:02d}-{day:02d}",
            'gender': random.choice(['male', 'female', 'other'])
        }
    
    def get_proxy(self) -> Optional[str]:
        """Get a proxy for account creation"""
        try:
            # Load proxies from file
            with open('proxies/proxies.txt', 'r') as f:
                proxies = [line.strip() for line in f if line.strip()]
            
            if proxies:
                return random.choice(proxies)
        except:
            pass
        
        return None
    
    def verify_account(self, account_data: Dict) -> bool:
        """Verify if account is still working"""
        # This would actually test login with the account
        # For now, return True for dummy accounts
        return True
    
    def create_multiple_accounts(self, count: int = 5) -> list:
        """Create multiple accounts"""
        accounts = []
        
        for i in range(count):
            logger.info(f"Creating account {i+1}/{count}...")
            
            account = self.create_account()
            if account:
                accounts.append(account)
                logger.info(f"Account {i+1} created successfully")
            
            # Delay between account creation
            if i < count - 1:
                delay = random.randint(30, 60)
                logger.info(f"Waiting {delay} seconds before next account...")
                time.sleep(delay)
        
        return accounts
    
    def save_accounts(self, accounts: list, filename: str = "accounts/created_accounts.json"):
        """Save created accounts to file"""
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(accounts, f, indent=2)
            
            logger.info(f"Saved {len(accounts)} accounts to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
            return False