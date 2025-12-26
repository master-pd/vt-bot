"""
Cookie Manager - Save, load, and manage browser cookies
"""

import json
import pickle
import time
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class CookieManager:
    def __init__(self, cookies_dir: str = "accounts/cookies"):
        self.cookies_dir = cookies_dir
        self.cookies = {}
        self.ensure_directory()
        self.load_all_cookies()
    
    def ensure_directory(self):
        """Ensure cookies directory exists"""
        os.makedirs(self.cookies_dir, exist_ok=True)
    
    def load_all_cookies(self):
        """Load all cookies from directory"""
        try:
            cookie_files = [f for f in os.listdir(self.cookies_dir) 
                          if f.endswith('.json') or f.endswith('.pkl')]
            
            for filename in cookie_files:
                account_id = filename.split('.')[0]
                filepath = os.path.join(self.cookies_dir, filename)
                
                try:
                    if filename.endswith('.json'):
                        with open(filepath, 'r') as f:
                            cookie_data = json.load(f)
                    else:  # .pkl
                        with open(filepath, 'rb') as f:
                            cookie_data = pickle.load(f)
                    
                    self.cookies[account_id] = cookie_data
                    logger.debug(f"Loaded cookies for account: {account_id}")
                    
                except Exception as e:
                    logger.error(f"Error loading cookies {filename}: {e}")
            
            logger.info(f"Loaded {len(self.cookies)} cookie files")
            
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            self.cookies = {}
    
    def save_cookies(self, account_id: str, cookies_data: Dict, format: str = "json") -> bool:
        """Save cookies for an account"""
        try:
            # Prepare cookie data
            cookie_info = {
                'account_id': account_id,
                'cookies': cookies_data,
                'saved_at': datetime.now().isoformat(),
                'cookie_count': len(cookies_data),
                'hash': self.calculate_cookie_hash(cookies_data)
            }
            
            # Determine filename
            if format == "json":
                filename = f"{account_id}.json"
                filepath = os.path.join(self.cookies_dir, filename)
                
                with open(filepath, 'w') as f:
                    json.dump(cookie_info, f, indent=2, default=str)
            else:  # pickle
                filename = f"{account_id}.pkl"
                filepath = os.path.join(self.cookies_dir, filename)
                
                with open(filepath, 'wb') as f:
                    pickle.dump(cookie_info, f)
            
            # Update cache
            self.cookies[account_id] = cookie_info
            
            logger.debug(f"Saved cookies for {account_id}: {len(cookies_data)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cookies for {account_id}: {e}")
            return False
    
    def load_cookies(self, account_id: str) -> Optional[Dict]:
        """Load cookies for an account"""
        # Check cache first
        if account_id in self.cookies:
            return self.cookies[account_id].get('cookies', {})
        
        # Try to load from file
        file_formats = ['.json', '.pkl']
        
        for fmt in file_formats:
            filename = f"{account_id}{fmt}"
            filepath = os.path.join(self.cookies_dir, filename)
            
            if os.path.exists(filepath):
                try:
                    if fmt == '.json':
                        with open(filepath, 'r') as f:
                            cookie_info = json.load(f)
                    else:  # .pkl
                        with open(filepath, 'rb') as f:
                            cookie_info = pickle.load(f)
                    
                    # Update cache
                    self.cookies[account_id] = cookie_info
                    
                    cookies = cookie_info.get('cookies', {})
                    logger.debug(f"Loaded {len(cookies)} cookies for {account_id}")
                    return cookies
                    
                except Exception as e:
                    logger.error(f"Error loading cookies from {filename}: {e}")
        
        logger.warning(f"No cookies found for account: {account_id}")
        return None
    
    def save_cookies_from_driver(self, driver, account_id: str, additional_data: Dict = None) -> bool:
        """Save cookies from Selenium WebDriver"""
        try:
            # Get cookies from driver
            driver_cookies = driver.get_cookies()
            
            # Convert to dictionary format
            cookies_dict = {}
            for cookie in driver_cookies:
                if 'name' in cookie and 'value' in cookie:
                    cookies_dict[cookie['name']] = {
                        'value': cookie['value'],
                        'domain': cookie.get('domain', ''),
                        'path': cookie.get('path', '/'),
                        'expiry': cookie.get('expiry'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    }
            
            # Prepare data
            cookie_data = {
                'cookies': cookies_dict,
                'user_agent': driver.execute_script("return navigator.userAgent"),
                'url': driver.current_url,
                'timestamp': time.time()
            }
            
            # Add additional data if provided
            if additional_data:
                cookie_data.update(additional_data)
            
            # Save cookies
            return self.save_cookies(account_id, cookie_data)
            
        except Exception as e:
            logger.error(f"Error saving cookies from driver for {account_id}: {e}")
            return False
    
    def load_cookies_to_driver(self, driver, account_id: str) -> bool:
        """Load cookies into Selenium WebDriver"""
        try:
            cookies_data = self.load_cookies(account_id)
            if not cookies_data:
                return False
            
            # Clear existing cookies
            driver.delete_all_cookies()
            
            # Add cookies to driver
            for cookie_name, cookie_info in cookies_data.items():
                if isinstance(cookie_info, dict):
                    # Convert to Selenium cookie format
                    cookie = {
                        'name': cookie_name,
                        'value': cookie_info.get('value', ''),
                        'domain': cookie_info.get('domain', '.tiktok.com'),
                        'path': cookie_info.get('path', '/'),
                        'secure': cookie_info.get('secure', True),
                        'httpOnly': cookie_info.get('httpOnly', False)
                    }
                    
                    # Add expiry if present
                    expiry = cookie_info.get('expiry')
                    if expiry:
                        cookie['expiry'] = int(expiry)
                    
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        logger.debug(f"Could not add cookie {cookie_name}: {e}")
            
            logger.debug(f"Loaded {len(cookies_data)} cookies to driver for {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading cookies to driver for {account_id}: {e}")
            return False
    
    def calculate_cookie_hash(self, cookies_data: Dict) -> str:
        """Calculate hash of cookies for change detection"""
        try:
            # Create string representation of cookies
            cookie_string = json.dumps(cookies_data, sort_keys=True)
            
            # Calculate MD5 hash
            return hashlib.md5(cookie_string.encode()).hexdigest()
        except:
            return ""
    
    def check_cookie_validity(self, account_id: str) -> Dict:
        """Check if cookies are still valid"""
        validity = {
            'account_id': account_id,
            'has_cookies': False,
            'cookie_count': 0,
            'cookie_age': 0,
            'is_expired': True,
            'ttl_seconds': 0
        }
        
        cookie_data = self.load_cookies(account_id)
        if not cookie_data:
            return validity
        
        validity['has_cookies'] = True
        validity['cookie_count'] = len(cookie_data)
        
        # Check for TikTok-specific cookies
        tiktok_cookies = ['sessionid', 'tt_chain_token', 'msToken', 'odin_tt']
        found_tiktok_cookies = [c for c in tiktok_cookies if c in cookie_data]
        validity['tiktok_cookies_found'] = len(found_tiktok_cookies)
        
        # Check cookie expiry
        current_time = time.time()
        soonest_expiry = float('inf')
        
        for cookie_name, cookie_info in cookie_data.items():
            if isinstance(cookie_info, dict):
                expiry = cookie_info.get('expiry')
                if expiry:
                    expiry_time = float(expiry)
                    soonest_expiry = min(soonest_expiry, expiry_time)
        
        if soonest_expiry != float('inf'):
            validity['cookie_age'] = current_time - soonest_expiry
            validity['is_expired'] = current_time > soonest_expiry
            validity['ttl_seconds'] = max(0, soonest_expiry - current_time)
        
        return validity
    
    def rotate_cookies(self, account_id: str, new_cookies: Dict) -> bool:
        """Rotate/update cookies for an account"""
        try:
            # Load existing cookies
            old_cookies = self.load_cookies(account_id) or {}
            
            # Merge cookies (new ones override old ones)
            merged_cookies = {**old_cookies, **new_cookies}
            
            # Save merged cookies
            return self.save_cookies(account_id, merged_cookies)
            
        except Exception as e:
            logger.error(f"Error rotating cookies for {account_id}: {e}")
            return False
    
    def backup_cookies(self, account_id: str, backup_dir: str = "accounts/cookies/backup") -> bool:
        """Create backup of cookies"""
        try:
            cookie_data = self.load_cookies(account_id)
            if not cookie_data:
                logger.warning(f"No cookies to backup for {account_id}")
                return False
            
            # Ensure backup directory exists
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{account_id}_{timestamp}.json")
            
            # Save backup
            backup_data = {
                'account_id': account_id,
                'cookies': cookie_data,
                'backup_time': datetime.now().isoformat(),
                'cookie_count': len(cookie_data)
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Backed up cookies for {account_id} to {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up cookies for {account_id}: {e}")
            return False
    
    def restore_cookies(self, account_id: str, backup_file: str = None) -> bool:
        """Restore cookies from backup"""
        try:
            if backup_file is None:
                # Find latest backup
                backup_dir = "accounts/cookies/backup"
                if not os.path.exists(backup_dir):
                    logger.error(f"Backup directory not found: {backup_dir}")
                    return False
                
                # Find backups for this account
                backup_files = [f for f in os.listdir(backup_dir) 
                              if f.startswith(f"{account_id}_") and f.endswith('.json')]
                
                if not backup_files:
                    logger.error(f"No backups found for {account_id}")
                    return False
                
                # Use latest backup
                backup_files.sort(reverse=True)
                backup_file = os.path.join(backup_dir, backup_files[0])
            
            # Load backup
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Restore cookies
            cookies = backup_data.get('cookies', {})
            if not cookies:
                logger.error(f"No cookies in backup file: {backup_file}")
                return False
            
            # Save restored cookies
            return self.save_cookies(account_id, cookies)
            
        except Exception as e:
            logger.error(f"Error restoring cookies for {account_id}: {e}")
            return False
    
    def cleanup_expired_cookies(self, max_age_days: int = 30):
        """Cleanup expired cookie files"""
        try:
            current_time = time.time()
            removed_count = 0
            
            for account_id, cookie_info in list(self.cookies.items()):
                saved_at = cookie_info.get('saved_at', '')
                
                if saved_at:
                    try:
                        # Parse timestamp
                        if isinstance(saved_at, str):
                            saved_time = datetime.fromisoformat(saved_at.replace('Z', '+00:00')).timestamp()
                        else:
                            saved_time = saved_at
                        
                        # Check age
                        age_days = (current_time - saved_time) / (24 * 3600)
                        
                        if age_days > max_age_days:
                            # Remove from cache
                            del self.cookies[account_id]
                            
                            # Remove file
                            file_formats = ['.json', '.pkl']
                            for fmt in file_formats:
                                filename = f"{account_id}{fmt}"
                                filepath = os.path.join(self.cookies_dir, filename)
                                
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                    logger.debug(f"Removed expired cookie file: {filename}")
                            
                            removed_count += 1
                    
                    except:
                        continue
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cookie files")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired cookies: {e}")
    
    def get_cookie_stats(self) -> Dict:
        """Get statistics about stored cookies"""
        stats = {
            'total_accounts': len(self.cookies),
            'total_cookies': 0,
            'accounts_with_cookies': 0,
            'avg_cookies_per_account': 0,
            'oldest_cookie_age': 0,
            'newest_cookie_age': 0
        }
        
        if not self.cookies:
            return stats
        
        # Calculate statistics
        total_cookies = 0
        cookie_ages = []
        current_time = time.time()
        
        for account_id, cookie_info in self.cookies.items():
            cookies = cookie_info.get('cookies', {})
            cookie_count = len(cookies)
            
            if cookie_count > 0:
                stats['accounts_with_cookies'] += 1
                total_cookies += cookie_count
            
            # Calculate age
            saved_at = cookie_info.get('saved_at', '')
            if saved_at:
                try:
                    if isinstance(saved_at, str):
                        saved_time = datetime.fromisoformat(saved_at.replace('Z', '+00:00')).timestamp()
                    else:
                        saved_time = saved_at
                    
                    age = current_time - saved_time
                    cookie_ages.append(age)
                except:
                    pass
        
        # Update stats
        stats['total_cookies'] = total_cookies
        
        if stats['accounts_with_cookies'] > 0:
            stats['avg_cookies_per_account'] = total_cookies / stats['accounts_with_cookies']
        
        if cookie_ages:
            stats['oldest_cookie_age'] = max(cookie_ages) / (24 * 3600)  # in days
            stats['newest_cookie_age'] = min(cookie_ages) / (24 * 3600)  # in days
        
        return stats
    
    def export_cookies(self, output_file: str = "cookies_export.json"):
        """Export all cookies to a file"""
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_accounts': len(self.cookies),
                'cookies': self.cookies
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Exported {len(self.cookies)} accounts to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting cookies: {e}")
            return False
    
    def import_cookies(self, import_file: str):
        """Import cookies from export file"""
        try:
            with open(import_file, 'r') as f:
                import_data = json.load(f)
            
            imported_cookies = import_data.get('cookies', {})
            imported_count = 0
            
            for account_id, cookie_info in imported_cookies.items():
                cookies = cookie_info.get('cookies', {})
                if cookies:
                    self.save_cookies(account_id, cookies)
                    imported_count += 1
            
            logger.info(f"Imported {imported_count} accounts from {import_file}")
            return True
        except Exception as e:
            logger.error(f"Error importing cookies: {e}")
            return False