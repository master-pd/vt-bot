"""
Screenshot utility for view verification
"""

import os
import time
import logging
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

class ScreenshotManager:
    def __init__(self, save_dir: str = "temp/screenshots"):
        self.save_dir = save_dir
        self.ensure_directory()
        
        # Try to load font
        try:
            self.font = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                self.font = ImageFont.load_default()
    
    def ensure_directory(self):
        """Ensure screenshot directory exists"""
        os.makedirs(self.save_dir, exist_ok=True)
    
    def capture_screenshot(self, driver, filename: Optional[str] = None) -> str:
        """
        Capture screenshot from WebDriver
        
        Args:
            driver: Selenium WebDriver instance
            filename: Optional filename
        
        Returns:
            Path to saved screenshot
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"screenshot_{timestamp}.png"
            
            filepath = os.path.join(self.save_dir, filename)
            
            # Capture screenshot
            screenshot_data = driver.get_screenshot_as_png()
            
            # Save to file
            with open(filepath, "wb") as f:
                f.write(screenshot_data)
            
            logger.debug(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return ""
    
    def capture_element_screenshot(self, driver, element, filename: Optional[str] = None) -> str:
        """
        Capture screenshot of specific element
        
        Args:
            driver: Selenium WebDriver instance
            element: WebElement to capture
            filename: Optional filename
        
        Returns:
            Path to saved screenshot
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"element_{timestamp}.png"
            
            filepath = os.path.join(self.save_dir, filename)
            
            # Get element location and size
            location = element.location
            size = element.size
            
            # Capture full screenshot
            full_screenshot = driver.get_screenshot_as_png()
            full_image = Image.open(io.BytesIO(full_screenshot))
            
            # Calculate cropping coordinates
            left = location['x']
            top = location['y']
            right = left + size['width']
            bottom = top + size['height']
            
            # Crop to element
            element_image = full_image.crop((left, top, right, bottom))
            
            # Save cropped image
            element_image.save(filepath)
            
            logger.debug(f"Element screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error capturing element screenshot: {e}")
            return ""
    
    def capture_view_count(self, driver, video_url: str, attempt: int = 1) -> str:
        """
        Capture screenshot of view count for verification
        
        Args:
            driver: Selenium WebDriver instance
            video_url: Video URL for naming
            attempt: Attempt number
        
        Returns:
            Path to saved screenshot
        """
        try:
            # Extract video ID for filename
            video_id = self.extract_video_id(video_url)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"views_{video_id}_{timestamp}_attempt{attempt}.png"
            filepath = os.path.join(self.save_dir, filename)
            
            # Find view count element
            view_elements = driver.find_elements(
                "xpath", 
                "//*[contains(text(), 'views') or contains(text(), 'Views') or @data-e2e='video-views']"
            )
            
            if view_elements:
                # Capture element screenshot
                return self.capture_element_screenshot(driver, view_elements[0], filename)
            else:
                # Capture full screenshot
                return self.capture_screenshot(driver, filename)
            
        except Exception as e:
            logger.error(f"Error capturing view count: {e}")
            return self.capture_screenshot(driver, f"error_{int(time.time())}.png")
    
    def extract_video_id(self, video_url: str) -> str:
        """Extract video ID from URL for naming"""
        try:
            # Simple extraction
            if "/video/" in video_url:
                parts = video_url.split("/video/")
                if len(parts) > 1:
                    video_id = parts[1].split("?")[0]
                    return video_id[:20]  # Limit length
            
            # Use timestamp as fallback
            return str(int(time.time()))
        except:
            return "unknown"
    
    def compare_screenshots(self, before_path: str, after_path: str, threshold: float = 0.95) -> Tuple[bool, float]:
        """
        Compare two screenshots for changes
        
        Args:
            before_path: Path to before screenshot
            after_path: Path to after screenshot
            threshold: Similarity threshold (0-1)
        
        Returns:
            Tuple of (changed: bool, similarity: float)
        """
        try:
            if not os.path.exists(before_path) or not os.path.exists(after_path):
                logger.error("Screenshot files not found")
                return False, 0.0
            
            # Load images
            before_img = Image.open(before_path).convert('RGB')
            after_img = Image.open(after_path).convert('RGB')
            
            # Ensure same size
            if before_img.size != after_img.size:
                # Resize to smallest
                min_width = min(before_img.width, after_img.width)
                min_height = min(before_img.height, after_img.height)
                
                before_img = before_img.resize((min_width, min_height))
                after_img = after_img.resize((min_width, min_height))
            
            # Convert to arrays
            before_pixels = list(before_img.getdata())
            after_pixels = list(after_img.getdata())
            
            # Calculate similarity
            total_pixels = len(before_pixels)
            same_pixels = 0
            
            for i in range(total_pixels):
                if before_pixels[i] == after_pixels[i]:
                    same_pixels += 1
            
            similarity = same_pixels / total_pixels
            
            # Determine if changed
            changed = similarity < threshold
            
            logger.debug(f"Screenshot similarity: {similarity:.2%}, Changed: {changed}")
            return changed, similarity
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {e}")
            return False, 0.0
    
    def annotate_screenshot(self, image_path: str, text: str, position: Tuple[int, int] = (10, 10)):
        """
        Add annotation/text to screenshot
        
        Args:
            image_path: Path to image
            text: Text to add
            position: (x, y) position
        """
        try:
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Add text background
            text_bbox = draw.textbbox(position, text, font=self.font)
            padding = 5
            draw.rectangle(
                [
                    text_bbox[0] - padding,
                    text_bbox[1] - padding,
                    text_bbox[2] + padding,
                    text_bbox[3] + padding
                ],
                fill="black"
            )
            
            # Add text
            draw.text(position, text, font=self.font, fill="white")
            
            # Save
            image.save(image_path)
            logger.debug(f"Added annotation to screenshot: {text}")
            
        except Exception as e:
            logger.error(f"Error annotating screenshot: {e}")
    
    def create_comparison_image(self, before_path: str, after_path: str, output_path: str):
        """
        Create side-by-side comparison image
        
        Args:
            before_path: Before screenshot
            after_path: After screenshot
            output_path: Output image path
        """
        try:
            before_img = Image.open(before_path)
            after_img = Image.open(after_path)
            
            # Resize to same height
            max_height = max(before_img.height, after_img.height)
            before_img = before_img.resize(
                (int(before_img.width * max_height / before_img.height), max_height)
            )
            after_img = after_img.resize(
                (int(after_img.width * max_height / after_img.height), max_height)
            )
            
            # Create new image
            total_width = before_img.width + after_img.width + 20
            comparison_img = Image.new('RGB', (total_width, max_height), 'white')
            
            # Paste images
            comparison_img.paste(before_img, (0, 0))
            comparison_img.paste(after_img, (before_img.width + 20, 0))
            
            # Add labels
            draw = ImageDraw.Draw(comparison_img)
            
            # Before label
            draw.text(
                (10, 10),
                "BEFORE",
                font=self.font,
                fill="red"
            )
            
            # After label
            draw.text(
                (before_img.width + 30, 10),
                "AFTER",
                font=self.font,
                fill="green"
            )
            
            # Add separator line
            draw.line(
                [(before_img.width + 10, 0), (before_img.width + 10, max_height)],
                fill="gray",
                width=2
            )
            
            # Save
            comparison_img.save(output_path)
            logger.debug(f"Comparison image created: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating comparison image: {e}")
            return ""
    
    def cleanup_old_screenshots(self, max_age_hours: int = 24):
        """Cleanup old screenshot files"""
        try:
            current_time = time.time()
            deleted_count = 0
            
            for filename in os.listdir(self.save_dir):
                filepath = os.path.join(self.save_dir, filename)
                
                # Get file age
                file_age = current_time - os.path.getmtime(filepath)
                
                # Delete if older than threshold
                if file_age > (max_age_hours * 3600):
                    os.remove(filepath)
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old screenshots")
                
        except Exception as e:
            logger.error(f"Error cleaning up screenshots: {e}")
    
    def get_screenshot_stats(self) -> dict:
        """Get screenshot statistics"""
        try:
            files = os.listdir(self.save_dir)
            image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            total_size = 0
            for filename in image_files:
                filepath = os.path.join(self.save_dir, filename)
                total_size += os.path.getsize(filepath)
            
            return {
                "total_screenshots": len(image_files),
                "total_size_mb": total_size / (1024 * 1024),
                "directory": self.save_dir
            }
            
        except Exception as e:
            logger.error(f"Error getting screenshot stats: {e}")
            return {}