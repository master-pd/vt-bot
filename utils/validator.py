"""
Advanced Input Validator
Professional validation utilities for all inputs
"""

import re
import json
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)

class Validator:
    """Advanced input validator"""
    
    # URL patterns
    TIKTOK_URL_PATTERNS = [
        r'https?://(?:www\.)?tiktok\.com/@[\w\.-]+/video/\d+',
        r'https?://(?:vm\.|vt\.)?tiktok\.com/[\w]+',
        r'tiktok\.com/@[\w\.-]+/video/\d+',
        r'@[\w\.-]+/video/\d+'
    ]
    
    # Email pattern
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Phone pattern (international)
    PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'
    
    # Username patterns
    TIKTOK_USERNAME_PATTERN = r'^@?[\w\.]{1,24}$'
    GENERIC_USERNAME_PATTERN = r'^[a-zA-Z0-9_.]{3,20}$'
    
    # Password strength requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIREMENTS = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': False
    }
    
    @staticmethod
    def validate_tiktok_url(url: str) -> Tuple[bool, str]:
        """
        Validate TikTok URL
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, normalized_url)
        """
        if not url:
            return False, ""
        
        url = url.strip()
        
        # Check against patterns
        for pattern in Validator.TIKTOK_URL_PATTERNS:
            if re.match(pattern, url, re.IGNORECASE):
                # Normalize URL
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Ensure www. prefix for consistency
                if 'tiktok.com' in url and not 'www.tiktok.com' in url:
                    url = url.replace('tiktok.com', 'www.tiktok.com')
                
                return True, url
        
        return False, ""
    
    @staticmethod
    def validate_view_count(count: Union[str, int], 
                           min_views: int = 1, 
                           max_views: int = 10000) -> Tuple[bool, int]:
        """
        Validate view count
        
        Args:
            count: View count to validate
            min_views: Minimum allowed views
            max_views: Maximum allowed views
            
        Returns:
            Tuple of (is_valid, parsed_count)
        """
        try:
            if isinstance(count, str):
                count = count.strip()
                if not count:
                    return False, 0
                
                # Remove commas and other non-digits
                count = ''.join(filter(str.isdigit, count))
                if not count:
                    return False, 0
                
                count = int(count)
            
            elif isinstance(count, int):
                pass
            else:
                return False, 0
            
            # Check bounds
            if min_views <= count <= max_views:
                return True, count
            else:
                return False, count
                
        except (ValueError, TypeError):
            return False, 0
    
    @staticmethod
    def validate_username(username: str, 
                         platform: str = 'generic') -> Tuple[bool, str]:
        """
        Validate username
        
        Args:
            username: Username to validate
            platform: Platform type ('tiktok' or 'generic')
            
        Returns:
            Tuple of (is_valid, normalized_username)
        """
        if not username:
            return False, ""
        
        username = username.strip()
        
        if platform.lower() == 'tiktok':
            pattern = Validator.TIKTOK_USERNAME_PATTERN
            # Remove @ prefix for validation
            if username.startswith('@'):
                username = username[1:]
        else:
            pattern = Validator.GENERIC_USERNAME_PATTERN
        
        if re.match(pattern, username):
            return True, username
        else:
            return False, username
    
    @staticmethod
    def validate_password(password: str, 
                         requirements: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            requirements: Password requirements dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if requirements is None:
            requirements = Validator.PASSWORD_REQUIREMENTS
        
        errors = []
        
        # Check length
        min_length = requirements.get('min_length', 8)
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters")
        
        # Check uppercase
        if requirements.get('require_uppercase', True):
            if not any(c.isupper() for c in password):
                errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase
        if requirements.get('require_lowercase', True):
            if not any(c.islower() for c in password):
                errors.append("Password must contain at least one lowercase letter")
        
        # Check digits
        if requirements.get('require_digits', True):
            if not any(c.isdigit() for c in password):
                errors.append("Password must contain at least one digit")
        
        # Check special characters
        if requirements.get('require_special', False):
            special_chars = r'!@#$%^&*()_+-=[]{}|;:,.<>?'
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False
        
        email = email.strip()
        
        if re.match(Validator.EMAIL_PATTERN, email, re.IGNORECASE):
            return True
        
        return False
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False
        
        phone = phone.strip()
        
        # Remove spaces, dashes, parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if re.match(Validator.PHONE_PATTERN, phone):
            return True
        
        return False
    
    @staticmethod
    def validate_proxy(proxy_url: str) -> Tuple[bool, Dict[str, str]]:
        """
        Validate proxy URL
        
        Args:
            proxy_url: Proxy URL to validate
            
        Returns:
            Tuple of (is_valid, proxy_info)
        """
        if not proxy_url:
            return False, {}
        
        proxy_url = proxy_url.strip()
        
        # Common proxy patterns
        patterns = {
            'http': r'^http://[\w\.-]+:\d+$',
            'https': r'^https://[\w\.-]+:\d+$',
            'socks4': r'^socks4://[\w\.-]+:\d+$',
            'socks5': r'^socks5://[\w\.-]+:\d+$'
        }
        
        proxy_info = {
            'url': proxy_url,
            'type': 'unknown',
            'host': '',
            'port': '',
            'valid': False
        }
        
        try:
            # Parse URL
            parsed = urllib.parse.urlparse(proxy_url)
            
            if not parsed.scheme or not parsed.netloc:
                return False, proxy_info
            
            # Extract host and port
            host = parsed.hostname
            port = parsed.port
            
            if not host:
                return False, proxy_info
            
            # Determine proxy type
            scheme = parsed.scheme.lower()
            if scheme in ['http', 'https', 'socks4', 'socks5']:
                proxy_info['type'] = scheme
            else:
                return False, proxy_info
            
            # Validate port
            if port and 1 <= port <= 65535:
                proxy_info['port'] = str(port)
            else:
                # Try to extract port from netloc
                if ':' in parsed.netloc:
                    try:
                        port_part = parsed.netloc.split(':')[1]
                        port = int(port_part)
                        if 1 <= port <= 65535:
                            proxy_info['port'] = str(port)
                        else:
                            return False, proxy_info
                    except (ValueError, IndexError):
                        return False, proxy_info
                else:
                    # Default ports
                    default_ports = {
                        'http': '80',
                        'https': '443',
                        'socks4': '1080',
                        'socks5': '1080'
                    }
                    proxy_info['port'] = default_ports.get(scheme, '')
            
            proxy_info['host'] = host
            proxy_info['valid'] = True
            
            return True, proxy_info
            
        except Exception as e:
            logger.debug(f"Proxy validation error: {e}")
            return False, proxy_info
    
    @staticmethod
    def validate_json(json_str: str, schema: Dict = None) -> Tuple[bool, Any]:
        """
        Validate JSON string
        
        Args:
            json_str: JSON string to validate
            schema: Optional JSON schema for validation
            
        Returns:
            Tuple of (is_valid, parsed_json)
        """
        if not json_str:
            return False, None
        
        try:
            parsed = json.loads(json_str)
            
            if schema:
                # Basic schema validation
                # For production, use a proper JSON schema validator like jsonschema
                return Validator._validate_json_schema(parsed, schema), parsed
            
            return True, parsed
            
        except json.JSONDecodeError as e:
            logger.debug(f"JSON validation error: {e}")
            return False, None
    
    @staticmethod
    def _validate_json_schema(data: Any, schema: Dict) -> bool:
        """
        Basic JSON schema validation
        
        Args:
            data: Data to validate
            schema: Schema definition
            
        Returns:
            True if valid, False otherwise
        """
        # This is a simplified schema validator
        # For production, use jsonschema library
        
        if not isinstance(data, type(schema.get('type', type(data)))):
            return False
        
        # Check required fields
        required_fields = schema.get('required', [])
        if isinstance(data, dict):
            for field in required_fields:
                if field not in data:
                    return False
        
        # Check enum values
        enum_values = schema.get('enum')
        if enum_values and data not in enum_values:
            return False
        
        # Check min/max for numbers
        if isinstance(data, (int, float)):
            min_val = schema.get('minimum')
            max_val = schema.get('maximum')
            
            if min_val is not None and data < min_val:
                return False
            
            if max_val is not None and data > max_val:
                return False
        
        # Check min/max length for strings
        if isinstance(data, str):
            min_length = schema.get('minLength')
            max_length = schema.get('maxLength')
            
            if min_length is not None and len(data) < min_length:
                return False
            
            if max_length is not None and len(data) > max_length:
                return False
        
        return True
    
    @staticmethod
    def sanitize_input(input_str: str, 
                      allowed_chars: str = None,
                      max_length: int = 1000) -> str:
        """
        Sanitize input to prevent XSS and injection attacks
        
        Args:
            input_str: Input string to sanitize
            allowed_chars: Characters to allow (regex pattern)
            max_length: Maximum length of output
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Convert to string
        input_str = str(input_str)
        
        # Trim whitespace
        input_str = input_str.strip()
        
        # Limit length
        if len(input_str) > max_length:
            input_str = input_str[:max_length]
        
        # Remove control characters
        input_str = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')
        
        # Escape HTML special characters
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        for char, escape in html_escape_table.items():
            input_str = input_str.replace(char, escape)
        
        # Filter by allowed characters if specified
        if allowed_chars:
            import re
            pattern = f'[^{re.escape(allowed_chars)}]'
            input_str = re.sub(pattern, '', input_str)
        
        return input_str
    
    @staticmethod
    def prevent_sql_injection(input_str: str) -> str:
        """
        Basic SQL injection prevention
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Common SQL injection patterns
        sql_patterns = [
            r'(?i)select.*from',
            r'(?i)insert.*into',
            r'(?i)update.*set',
            r'(?i)delete.*from',
            r'(?i)drop.*table',
            r'(?i)union.*select',
            r'(?i)or.*=.*',
            r'(?i)and.*=.*',
            r'--',
            r';',
            r'/\*',
            r'\*/'
        ]
        
        for pattern in sql_patterns:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE)
        
        # Remove quotes
        input_str = input_str.replace("'", "")
        input_str = input_str.replace('"', "")
        input_str = input_str.replace("`", "")
        
        return input_str
    
    @staticmethod
    def validate_date(date_str: str, 
                     format: str = "%Y-%m-%d") -> Tuple[bool, datetime]:
        """
        Validate date string
        
        Args:
            date_str: Date string to validate
            format: Expected date format
            
        Returns:
            Tuple of (is_valid, datetime_object)
        """
        if not date_str:
            return False, None
        
        try:
            date_obj = datetime.strptime(date_str, format)
            return True, date_obj
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_number(number_str: str, 
                       min_val: float = None,
                       max_val: float = None) -> Tuple[bool, float]:
        """
        Validate number string
        
        Args:
            number_str: Number string to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, parsed_number)
        """
        if not number_str:
            return False, 0.0
        
        try:
            # Remove commas and whitespace
            number_str = str(number_str).strip().replace(',', '')
            
            # Try to parse as float
            number = float(number_str)
            
            # Check bounds
            if min_val is not None and number < min_val:
                return False, number
            
            if max_val is not None and number > max_val:
                return False, number
            
            return True, number
            
        except (ValueError, TypeError):
            return False, 0.0
    
    @staticmethod
    def validate_file_extension(filename: str, 
                               allowed_extensions: List[str]) -> bool:
        """
        Validate file extension
        
        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions
            
        Returns:
            True if valid, False otherwise
        """
        if not filename:
            return False
        
        # Get file extension
        if '.' in filename:
            ext = filename.lower().split('.')[-1]
            return ext in [ext.lower() for ext in allowed_extensions]
        
        return False
    
    @staticmethod
    def validate_ip_address(ip_str: str) -> bool:
        """
        Validate IP address
        
        Args:
            ip_str: IP address string to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not ip_str:
            return False
        
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        match = re.match(ipv4_pattern, ip_str)
        if match:
            # Check each octet
            for octet in match.groups():
                if not 0 <= int(octet) <= 255:
                    return False
            return True
        
        # IPv6 pattern (simplified)
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        if re.match(ipv6_pattern, ip_str):
            return True
        
        return False
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """
        Validate domain name
        
        Args:
            domain: Domain name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not domain:
            return False
        
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
        
        return bool(re.match(domain_pattern, domain))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate general URL
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not url:
            return False
        
        url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?(?:/[-\w%.]*)*$'
        
        return bool(re.match(url_pattern, url, re.IGNORECASE))