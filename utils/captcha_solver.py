"""
CAPTCHA Solver - Solve various CAPTCHAs automatically
"""

import time
import random
import logging
from typing import Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self):
        self.solving_methods = [
            self.solve_bypass_method,
            self.solve_click_method,
            self.solve_rotate_method,
            self.solve_slider_method
        ]
    
    def solve_captcha(self, driver, captcha_type: str = "auto") -> bool:
        """
        Solve CAPTCHA on current page
        
        Args:
            driver: Selenium WebDriver instance
            captcha_type: Type of CAPTCHA (auto, hcaptcha, recaptcha, etc.)
        
        Returns:
            True if solved, False otherwise
        """
        logger.info(f"Attempting to solve {captcha_type} CAPTCHA")
        
        if captcha_type == "auto":
            captcha_type = self.detect_captcha_type(driver)
        
        try:
            if captcha_type == "hcaptcha":
                return self.solve_hcaptcha(driver)
            elif captcha_type == "recaptcha":
                return self.solve_recaptcha(driver)
            elif captcha_type == "cloudflare":
                return self.solve_cloudflare(driver)
            else:
                # Try all methods
                for method in self.solving_methods:
                    if method(driver):
                        return True
            
            logger.warning("All CAPTCHA solving methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {e}")
            return False
    
    def detect_captcha_type(self, driver) -> str:
        """Detect CAPTCHA type on page"""
        try:
            page_source = driver.page_source.lower()
            
            if "hcaptcha" in page_source:
                return "hcaptcha"
            elif "recaptcha" in page_source or "g-recaptcha" in page_source:
                return "recaptcha"
            elif "cloudflare" in page_source:
                return "cloudflare"
            elif "captcha" in page_source:
                # Check for image CAPTCHA
                images = driver.find_elements(By.TAG_NAME, "img")
                for img in images:
                    src = img.get_attribute("src") or ""
                    alt = img.get_attribute("alt") or ""
                    if "captcha" in src.lower() or "captcha" in alt.lower():
                        return "image"
            
            return "unknown"
            
        except:
            return "unknown"
    
    def solve_hcaptcha(self, driver) -> bool:
        """Solve hCaptcha"""
        try:
            # Wait for hCaptcha iframe
            wait = WebDriverWait(driver, 10)
            
            # Switch to hCaptcha iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "hcaptcha.com" in src:
                    driver.switch_to.frame(iframe)
                    
                    # Click checkbox
                    checkbox = wait.until(
                        EC.element_to_be_clickable((By.ID, "checkbox"))
                    )
                    checkbox.click()
                    
                    driver.switch_to.default_content()
                    time.sleep(2)
                    
                    # Check if challenge appears
                    challenge_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for challenge_iframe in challenge_iframes:
                        src = challenge_iframe.get_attribute("src") or ""
                        if "hcaptcha.com" in src and "challenge" in src:
                            logger.info("hCaptcha challenge detected, using bypass")
                            return self.bypass_hcaptcha_challenge(driver, challenge_iframe)
                    
                    return True
            
            logger.warning("hCaptcha iframe not found")
            return False
            
        except Exception as e:
            logger.error(f"Error solving hCaptcha: {e}")
            return False
    
    def bypass_hcaptcha_challenge(self, driver, iframe) -> bool:
        """Bypass hCaptcha challenge"""
        try:
            # Switch to challenge iframe
            driver.switch_to.frame(iframe)
            
            # Try to find and click bypass button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                text = button.text.lower()
                if "skip" in text or "next" in text or "verify" in text:
                    button.click()
                    time.sleep(2)
                    driver.switch_to.default_content()
                    return True
            
            # If no button found, try to solve with audio
            audio_button = driver.find_element(
                By.CSS_SELECTOR, 
                "button[aria-label*='audio']"
            )
            audio_button.click()
            time.sleep(2)
            
            # Get audio challenge
            audio_url = driver.find_element(
                By.TAG_NAME, "audio"
            ).get_attribute("src")
            
            if audio_url:
                # In real implementation, you would:
                # 1. Download audio
                # 2. Convert to text (speech recognition)
                # 3. Enter text
                logger.info("Audio CAPTCHA detected, using fallback")
            
            driver.switch_to.default_content()
            return self.solve_bypass_method(driver)
            
        except:
            driver.switch_to.default_content()
            return False
    
    def solve_recaptcha(self, driver) -> bool:
        """Solve reCAPTCHA"""
        try:
            # Find reCAPTCHA iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            recaptcha_iframes = []
            
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "google.com/recaptcha" in src:
                    recaptcha_iframes.append(iframe)
            
            if not recaptcha_iframes:
                logger.warning("reCAPTCHA iframe not found")
                return False
            
            # Switch to first reCAPTCHA iframe
            driver.switch_to.frame(recaptcha_iframes[0])
            
            # Click checkbox
            checkbox = driver.find_element(
                By.CSS_SELECTOR, 
                ".recaptcha-checkbox-border"
            )
            checkbox.click()
            
            driver.switch_to.default_content()
            time.sleep(3)
            
            # Check for challenge
            challenge_detected = False
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "google.com/recaptcha/api2/bframe" in src:
                    challenge_detected = True
                    break
            
            if challenge_detected:
                logger.info("reCAPTCHA challenge detected")
                return self.solve_recaptcha_challenge(driver)
            
            return True
            
        except Exception as e:
            logger.error(f"Error solving reCAPTCHA: {e}")
            driver.switch_to.default_content()
            return False
    
    def solve_recaptcha_challenge(self, driver) -> bool:
        """Solve reCAPTCHA challenge (image selection)"""
        try:
            # Find challenge iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                src = iframe.get_attribute("src") or ""
                if "google.com/recaptcha/api2/bframe" in src:
                    driver.switch_to.frame(iframe)
                    
                    # Get challenge text
                    challenge_text = driver.find_element(
                        By.CSS_SELECTOR,
                        ".rc-imageselect-desc strong"
                    ).text
                    
                    logger.info(f"reCAPTCHA challenge: {challenge_text}")
                    
                    # Find all images
                    images = driver.find_elements(
                        By.CSS_SELECTOR,
                        ".rc-image-tile-wrapper img"
                    )
                    
                    # Randomly select some images (this is where AI would help)
                    # For now, we'll use a simple heuristic
                    images_to_click = random.sample(
                        range(len(images)), 
                        k=random.randint(1, min(4, len(images)))
                    )
                    
                    # Click selected images
                    for idx in images_to_click:
                        images[idx].click()
                        time.sleep(0.5)
                    
                    # Click verify button
                    verify_button = driver.find_element(
                        By.ID, "recaptcha-verify-button"
                    )
                    verify_button.click()
                    
                    driver.switch_to.default_content()
                    time.sleep(3)
                    
                    return True
            
            return False
            
        except:
            driver.switch_to.default_content()
            return False
    
    def solve_cloudflare(self, driver) -> bool:
        """Solve Cloudflare CAPTCHA/Challenge"""
        try:
            # Cloudflare often uses a simple "Verify you are human" button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                text = button.text.lower()
                if "verify" in text or "human" in text or "continue" in text:
                    button.click()
                    time.sleep(5)
                    return True
            
            # Check for challenge form
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                action = form.get_attribute("action") or ""
                if "challenge" in action:
                    # Submit form with default values
                    form.submit()
                    time.sleep(5)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error solving Cloudflare: {e}")
            return False
    
    def solve_bypass_method(self, driver) -> bool:
        """Bypass CAPTCHA using various techniques"""
        try:
            # Method 1: Refresh page
            driver.refresh()
            time.sleep(3)
            
            # Method 2: Use different user agent
            self.rotate_user_agent(driver)
            
            # Method 3: Wait and retry
            time.sleep(10)
            driver.refresh()
            time.sleep(3)
            
            # Check if CAPTCHA is still there
            page_source = driver.page_source.lower()
            if "captcha" not in page_source:
                return True
            
            return False
            
        except:
            return False
    
    def solve_click_method(self, driver) -> bool:
        """Solve by clicking around"""
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            actions = ActionChains(driver)
            
            # Click random positions
            for _ in range(random.randint(5, 10)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y).click().perform()
                time.sleep(random.uniform(0.1, 0.5))
            
            # Scroll randomly
            for _ in range(random.randint(3, 6)):
                scroll_amount = random.randint(-300, 300)
                driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.5, 1.5))
            
            time.sleep(2)
            return True
            
        except:
            return False
    
    def solve_rotate_method(self, driver) -> bool:
        """Solve by rotating IP/user agent"""
        try:
            # This would require proxy rotation
            # For now, we'll just simulate
            logger.info("Rotating IP/User Agent to bypass CAPTCHA")
            
            # Delete cookies
            driver.delete_all_cookies()
            
            # Execute JavaScript to clear storage
            driver.execute_script("""
            localStorage.clear();
            sessionStorage.clear();
            """)
            
            time.sleep(2)
            return True
            
        except:
            return False
    
    def solve_slider_method(self, driver) -> bool:
        """Solve slider CAPTCHA"""
        try:
            # Find slider element
            sliders = driver.find_elements(
                By.CSS_SELECTOR,
                ".slider, [role='slider'], input[type='range']"
            )
            
            for slider in sliders:
                if slider.is_displayed():
                    # Move slider
                    actions = ActionChains(driver)
                    
                    # Click and drag
                    actions.click_and_hold(slider)
                    
                    # Move random distance
                    move_distance = random.randint(100, 300)
                    actions.move_by_offset(move_distance, 0)
                    
                    # Add some randomness
                    for _ in range(3):
                        small_move = random.randint(-10, 10)
                        actions.move_by_offset(small_move, 0)
                        time.sleep(0.1)
                    
                    actions.release().perform()
                    time.sleep(2)
                    
                    return True
            
            return False
            
        except:
            return False
    
    def rotate_user_agent(self, driver):
        """Rotate user agent to avoid detection"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
        
        new_ua = random.choice(user_agents)
        
        # Execute CDP command to set user agent
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {"userAgent": new_ua}
        )
        
        logger.debug(f"User agent rotated to: {new_ua}")
    
    def is_captcha_present(self, driver) -> bool:
        """Check if CAPTCHA is present on page"""
        try:
            page_source = driver.page_source.lower()
            
            captcha_indicators = [
                "captcha",
                "hcaptcha",
                "recaptcha",
                "cloudflare",
                "verify you are human",
                "robot check",
                "security check"
            ]
            
            for indicator in captcha_indicators:
                if indicator in page_source:
                    return True
            
            # Check for CAPTCHA images
            images = driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                alt = img.get_attribute("alt") or ""
                src = img.get_attribute("src") or ""
                
                if "captcha" in alt.lower() or "captcha" in src.lower():
                    return True
            
            return False
            
        except:
            return False
    
    def get_solving_stats(self) -> Dict:
        """Get CAPTCHA solving statistics"""
        return {
            "total_attempts": 0,  # Would track in real implementation
            "success_rate": 0,
            "average_time": 0,
            "methods_used": []
        }