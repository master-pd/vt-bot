"""
OCR Tools - Optical Character Recognition for view count extraction
"""

import os
import time
import logging
from typing import Optional, Tuple, List
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class OCRTools:
    def __init__(self):
        self.tesseract_path = None
        self.setup_tesseract()
        
        # View count patterns
        self.view_patterns = [
            r'(\d+[\.,]?\d*)\s*(views|view|Views|View)',
            r'(\d+[\.,]?\d*)\s*(次观看|次觀看|回視聴)',
            r'Views\s*:\s*(\d+[\.,]?\d*)',
            r'(\d+[\.,]?\d*)\s*回',
            r'(\d+[,\d]*)\s*visualizzazioni',
            r'(\d+[,\d]*)\s*reproducciones',
            r'(\d+[,\d]*)\s*visualizações'
        ]
        
        # Number recognition patterns
        self.number_patterns = [
            r'\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b',  # Standard numbers
            r'\b\d+[kKmM]?\b',  # Numbers with k/M suffix
            r'\b\d+\s*[万千]?\b'  # Chinese/Japanese numbers
        ]
        
        # Image preprocessing settings
        self.preprocess_config = {
            'resize_factor': 2.0,
            'contrast_factor': 1.5,
            'brightness_factor': 1.2,
            'sharpness_factor': 2.0,
            'threshold_value': 150,
            'blur_radius': 1
        }
    
    def setup_tesseract(self):
        """Setup Tesseract OCR paths"""
        try:
            import pytesseract
            
            # Try to find Tesseract in common locations
            possible_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                '/opt/homebrew/bin/tesseract',
                'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
                'C:\\Tesseract-OCR\\tesseract.exe'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_path = path
                    logger.info(f"Tesseract found at: {path}")
                    return True
            
            # Try system PATH
            try:
                pytesseract.get_tesseract_version()
                logger.info("Tesseract found in system PATH")
                return True
            except:
                logger.warning("Tesseract not found. OCR functionality will be limited.")
                return False
                
        except ImportError:
            logger.error("pytesseract not installed. Install with: pip install pytesseract")
            return False
    
    def extract_view_count(self, image_path: str) -> Optional[int]:
        """
        Extract view count from screenshot
        
        Args:
            image_path: Path to screenshot image
        
        Returns:
            View count as integer, or None if not found
        """
        logger.debug(f"Extracting view count from: {image_path}")
        
        try:
            # Load and preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return None
            
            # Try multiple OCR methods
            view_count = None
            
            # Method 1: Direct OCR with pytesseract
            if self.tesseract_path:
                view_count = self.ocr_with_tesseract(processed_image)
            
            # Method 2: Template matching (fallback)
            if view_count is None:
                view_count = self.template_matching(processed_image)
            
            # Method 3: Custom digit recognition
            if view_count is None:
                view_count = self.custom_digit_recognition(processed_image)
            
            if view_count is not None:
                logger.info(f"Extracted view count: {view_count:,}")
            else:
                logger.warning("Could not extract view count")
            
            return view_count
            
        except Exception as e:
            logger.error(f"Error extracting view count: {e}")
            return None
    
    def preprocess_image(self, image_path: str) -> Optional[Image.Image]:
        """Preprocess image for better OCR results"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize for better OCR
            width, height = image.size
            new_size = (int(width * self.preprocess_config['resize_factor']), 
                       int(height * self.preprocess_config['resize_factor']))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(self.preprocess_config['contrast_factor'])
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.preprocess_config['brightness_factor'])
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(self.preprocess_config['sharpness_factor'])
            
            # Apply threshold
            image = image.point(lambda x: 0 if x < self.preprocess_config['threshold_value'] else 255)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.GaussianBlur(
                self.preprocess_config['blur_radius']
            ))
            
            # Save processed image for debugging
            debug_dir = "temp/ocr_debug"
            os.makedirs(debug_dir, exist_ok=True)
            debug_path = os.path.join(debug_dir, f"processed_{int(time.time())}.png")
            image.save(debug_path)
            logger.debug(f"Saved processed image: {debug_path}")
            
            return image
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    def ocr_with_tesseract(self, image: Image.Image) -> Optional[int]:
        """Extract text using Tesseract OCR"""
        try:
            import pytesseract
            import re
            
            # Configure Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789,kKmM viewsView次觀看視聴万千'
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=custom_config)
            logger.debug(f"OCR extracted text: {text}")
            
            # Try to find view count in text
            view_count = self.find_view_count_in_text(text)
            
            if view_count:
                return view_count
            
            # If not found with custom config, try with default
            text = pytesseract.image_to_string(image)
            logger.debug(f"OCR extracted text (default): {text}")
            
            return self.find_view_count_in_text(text)
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return None
    
    def find_view_count_in_text(self, text: str) -> Optional[int]:
        """Find view count in OCR text"""
        import re
        
        # Clean text
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Try each pattern
        for pattern in self.view_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number_str = match.group(1)
                return self.parse_number_string(number_str)
        
        # Try generic number patterns
        for pattern in self.number_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Heuristic: view counts are usually larger numbers
                number = self.parse_number_string(match)
                if number and number >= 100:  # Reasonable minimum for views
                    return number
        
        return None
    
    def parse_number_string(self, number_str: str) -> Optional[int]:
        """Parse number string with various formats"""
        try:
            # Clean string
            number_str = number_str.strip().replace(',', '').replace('.', '')
            
            # Handle k/M suffixes
            if number_str.lower().endswith('k'):
                number = float(number_str[:-1]) * 1000
            elif number_str.lower().endswith('m'):
                number = float(number_str[:-1]) * 1000000
            elif number_str.lower().endswith('万'):  # Chinese 10,000
                number = float(number_str[:-1]) * 10000
            elif number_str.lower().endswith('千'):  # Chinese 1,000
                number = float(number_str[:-1]) * 1000
            else:
                number = float(number_str)
            
            return int(number)
            
        except:
            return None
    
    def template_matching(self, image: Image.Image) -> Optional[int]:
        """Extract numbers using template matching"""
        try:
            import cv2
            
            # Convert PIL to OpenCV format
            open_cv_image = np.array(image)
            
            # Convert to grayscale if needed
            if len(open_cv_image.shape) == 3:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
            
            # Threshold image
            _, thresh = cv2.threshold(open_cv_image, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size (looking for digits)
            digit_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by aspect ratio and size (typical digits)
                aspect_ratio = w / h
                if 0.2 < aspect_ratio < 1.0 and h > 20 and w > 10:
                    digit_contours.append((x, y, w, h))
            
            # Sort contours left to right
            digit_contours.sort(key=lambda c: c[0])
            
            # Extract digits (simplified - would need digit templates)
            # This is a basic implementation
            if len(digit_contours) >= 3:  # Reasonable minimum for view count
                # For now, return a placeholder
                # In full implementation, you would match against digit templates
                logger.debug(f"Found {len(digit_contours)} potential digit contours")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Template matching error: {e}")
            return None
    
    def custom_digit_recognition(self, image: Image.Image) -> Optional[int]:
        """Custom digit recognition using feature matching"""
        try:
            # This would require trained digit templates
            # For now, use a simplified approach
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Look for common digit patterns
            # This is very simplified - real implementation would use ML
            
            return None
            
        except Exception as e:
            logger.error(f"Custom digit recognition error: {e}")
            return None
    
    def compare_view_counts(self, before_image: str, after_image: str) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """
        Compare view counts from two screenshots
        
        Returns:
            Tuple of (before_count, after_count, difference)
        """
        try:
            logger.info("Comparing view counts...")
            
            # Extract view counts
            before_count = self.extract_view_count(before_image)
            after_count = self.extract_view_count(after_image)
            
            # Calculate difference
            difference = None
            if before_count is not None and after_count is not None:
                difference = after_count - before_count
            
            logger.info(f"View count comparison: {before_count} → {after_count} (Δ: {difference})")
            
            return before_count, after_count, difference
            
        except Exception as e:
            logger.error(f"Error comparing view counts: {e}")
            return None, None, None
    
    def verify_view_increase(self, before_image: str, after_image: str, 
                           min_increase: int = 1, timeout: int = 300) -> Tuple[bool, Dict]:
        """
        Verify that views increased between screenshots
        
        Args:
            before_image: Path to before screenshot
            after_image: Path to after screenshot
            min_increase: Minimum increase to consider successful
            timeout: Maximum time to wait for increase
        
        Returns:
            Tuple of (success: bool, details: Dict)
        """
        start_time = time.time()
        details = {
            'success': False,
            'before_count': None,
            'after_count': None,
            'difference': None,
            'time_taken': 0,
            'iterations': 0
        }
        
        logger.info(f"Verifying view increase (min: {min_increase}, timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            details['iterations'] += 1
            
            # Extract counts
            before_count, after_count, difference = self.compare_view_counts(
                before_image, after_image
            )
            
            details['before_count'] = before_count
            details['after_count'] = after_count
            details['difference'] = difference
            
            # Check if increase meets minimum
            if (difference is not None and difference >= min_increase and
                before_count is not None and after_count is not None):
                
                details['success'] = True
                details['time_taken'] = time.time() - start_time
                
                logger.info(f"✅ View increase verified: +{difference} views "
                          f"({before_count} → {after_count}) in {details['time_taken']:.1f}s")
                
                return True, details
            
            # Wait before retry
            wait_time = min(10, timeout - (time.time() - start_time))
            if wait_time > 0:
                logger.debug(f"View increase not detected yet. Waiting {wait_time}s...")
                time.sleep(wait_time)
        
        details['time_taken'] = time.time() - start_time
        logger.warning(f"❌ View increase verification failed after {details['time_taken']:.1f}s")
        
        return False, details
    
    def batch_process_screenshots(self, screenshot_dir: str) -> List[Dict]:
        """
        Process all screenshots in directory
        
        Returns:
            List of processing results
        """
        results = []
        
        try:
            # Find all image files
            image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
            image_files = []
            
            for file in os.listdir(screenshot_dir):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    image_files.append(os.path.join(screenshot_dir, file))
            
            logger.info(f"Found {len(image_files)} images to process")
            
            # Process each image
            for image_path in image_files:
                try:
                    view_count = self.extract_view_count(image_path)
                    
                    result = {
                        'filename': os.path.basename(image_path),
                        'path': image_path,
                        'view_count': view_count,
                        'timestamp': datetime.fromtimestamp(os.path.getmtime(image_path)),
                        'success': view_count is not None
                    }
                    
                    results.append(result)
                    
                    logger.debug(f"Processed {result['filename']}: {view_count}")
                    
                except Exception as e:
                    logger.error(f"Error processing {image_path}: {e}")
            
            # Sort by timestamp
            results.sort(key=lambda x: x['timestamp'])
            
            # Calculate statistics
            successful = sum(1 for r in results if r['success'])
            total_counts = [r['view_count'] for r in results if r['view_count'] is not None]
            
            stats = {
                'total_images': len(results),
                'successful_extractions': successful,
                'success_rate': successful / len(results) if results else 0,
                'min_views': min(total_counts) if total_counts else None,
                'max_views': max(total_counts) if total_counts else None,
                'avg_views': sum(total_counts) / len(total_counts) if total_counts else None
            }
            
            logger.info(f"Batch processing complete: {stats['success_rate']:.1%} success rate")
            
            return results, stats
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return [], {}
    
    def create_view_timeline(self, screenshot_dir: str) -> List[Dict]:
        """Create timeline of view counts from screenshots"""
        results, stats = self.batch_process_screenshots(screenshot_dir)
        
        timeline = []
        for result in results:
            if result['success']:
                timeline.append({
                    'time': result['timestamp'].isoformat(),
                    'views': result['view_count'],
                    'filename': result['filename']
                })
        
        # Sort by time
        timeline.sort(key=lambda x: x['time'])
        
        # Calculate view increase between points
        for i in range(1, len(timeline)):
            prev_views = timeline[i-1]['views']
            curr_views = timeline[i]['views']
            timeline[i]['increase'] = curr_views - prev_views
            timeline[i]['increase_percent'] = ((curr_views - prev_views) / prev_views * 100) if prev_views > 0 else 0
        
        return timeline, stats
    
    def save_ocr_results(self, results: List[Dict], output_file: str = "ocr_results.json"):
        """Save OCR results to file"""
        try:
            import json
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Saved OCR results to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving OCR results: {e}")
            return False