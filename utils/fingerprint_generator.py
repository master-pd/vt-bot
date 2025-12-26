"""
Fingerprint Generator - Generate unique browser fingerprints
"""

import random
import json
import hashlib
import logging
from typing import Dict, List, Optional
import platform
import sys

logger = logging.getLogger(__name__)

class FingerprintGenerator:
    def __init__(self):
        # Browser fingerprints database
        self.browser_profiles = self.load_browser_profiles()
        
        # Canvas fingerprinting patterns
        self.canvas_patterns = [
            "rgba-gradient",
            "arcs-complex",
            "texture-noise",
            "geometric-pattern",
            "wave-interference"
        ]
        
        # WebGL renderers
        self.webgl_renderers = [
            "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (AMD Radeon(TM) Vega 8 Graphics Direct3D11 vs_5_0 ps_5_0)",
            "ANGLE (NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0)",
            "WebKit WebGL",
            "Mozilla WebGL"
        ]
        
        # Audio context fingerprints
        self.audio_contexts = [
            "OscillatorNode",
            "AnalyserNode",
            "GainNode",
            "DelayNode",
            "BiquadFilterNode"
        ]
    
    def load_browser_profiles(self) -> List[Dict]:
        """Load browser fingerprint profiles"""
        return [
            {
                "name": "Chrome_Windows",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "platform": "Win32",
                "language": "en-US",
                "languages": ["en-US", "en"],
                "hardwareConcurrency": 8,
                "deviceMemory": 8,
                "screenResolution": "1920x1080",
                "colorDepth": 24,
                "pixelDepth": 24,
                "timezone": "America/New_York",
                "timezoneOffset": -300
            },
            {
                "name": "Firefox_Mac",
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
                "platform": "MacIntel",
                "language": "en-US",
                "languages": ["en-US", "en"],
                "hardwareConcurrency": 12,
                "deviceMemory": 16,
                "screenResolution": "2560x1600",
                "colorDepth": 30,
                "pixelDepth": 30,
                "timezone": "America/Los_Angeles",
                "timezoneOffset": -480
            },
            {
                "name": "Safari_iOS",
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
                "platform": "iPhone",
                "language": "en-US",
                "languages": ["en-US", "en"],
                "hardwareConcurrency": 6,
                "deviceMemory": 4,
                "screenResolution": "1170x2532",
                "colorDepth": 24,
                "pixelDepth": 24,
                "timezone": "America/Chicago",
                "timezoneOffset": -360
            },
            {
                "name": "Chrome_Android",
                "userAgent": "Mozilla/5.0 (Linux; Android 13; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "platform": "Linux armv81",
                "language": "en-US",
                "languages": ["en-US", "en"],
                "hardwareConcurrency": 8,
                "deviceMemory": 8,
                "screenResolution": "1080x2400",
                "colorDepth": 24,
                "pixelDepth": 24,
                "timezone": "Europe/London",
                "timezoneOffset": 0
            }
        ]
    
    def generate_fingerprint(self, profile_name: str = None) -> Dict:
        """Generate a complete browser fingerprint"""
        if profile_name:
            # Use specific profile
            profile = next((p for p in self.browser_profiles if p['name'] == profile_name), 
                          random.choice(self.browser_profiles))
        else:
            # Random profile
            profile = random.choice(self.browser_profiles)
        
        # Generate fingerprint
        fingerprint = {
            'basic': self.generate_basic_fingerprint(profile),
            'canvas': self.generate_canvas_fingerprint(),
            'webgl': self.generate_webgl_fingerprint(),
            'audio': self.generate_audio_fingerprint(),
            'fonts': self.generate_font_fingerprint(),
            'plugins': self.generate_plugin_fingerprint(),
            'time': self.generate_time_fingerprint(),
            'hash': ''
        }
        
        # Calculate overall hash
        fingerprint['hash'] = self.calculate_fingerprint_hash(fingerprint)
        
        logger.debug(f"Generated fingerprint: {fingerprint['hash'][:16]}...")
        return fingerprint
    
    def generate_basic_fingerprint(self, profile: Dict) -> Dict:
        """Generate basic browser fingerprint"""
        basic = profile.copy()
        
        # Add dynamic values
        basic['userAgent'] = self.modify_user_agent(profile['userAgent'])
        basic['platform'] = self.modify_platform(profile['platform'])
        basic['hardwareConcurrency'] = random.choice([2, 4, 6, 8, 12, 16])
        basic['deviceMemory'] = random.choice([2, 4, 8, 16, 32])
        
        # Screen properties with slight variations
        if 'x' in profile['screenResolution']:
            width, height = map(int, profile['screenResolution'].split('x'))
            width += random.randint(-10, 10)
            height += random.randint(-10, 10)
            basic['screenResolution'] = f"{width}x{height}"
        
        # Color depth variations
        basic['colorDepth'] = random.choice([24, 30, 32])
        basic['pixelDepth'] = basic['colorDepth']
        
        # Timezone with slight offset variations
        basic['timezoneOffset'] += random.randint(-30, 30)
        
        # Additional properties
        basic['cookieEnabled'] = True
        basic['doNotTrack'] = random.choice([None, '1', '0'])
        basic['javaEnabled'] = False
        basic['pdfViewerEnabled'] = True
        basic['webdriver'] = False
        
        return basic
    
    def modify_user_agent(self, base_ua: str) -> str:
        """Modify user agent with slight variations"""
        parts = base_ua.split(' ')
        
        # Chrome version variations
        if 'Chrome/' in base_ua:
            for i, part in enumerate(parts):
                if part.startswith('Chrome/'):
                    version = part.split('/')[1]
                    major = int(version.split('.')[0])
                    # Slight version variations
                    new_major = max(100, min(120, major + random.randint(-5, 0)))
                    parts[i] = f"Chrome/{new_major}.0.0.0"
        
        # Firefox version variations
        elif 'Firefox/' in base_ua:
            for i, part in enumerate(parts):
                if part.startswith('Firefox/'):
                    version = part.split('/')[1]
                    major = int(version.split('.')[0])
                    new_major = max(110, min(121, major + random.randint(-5, 0)))
                    parts[i] = f"Firefox/{new_major}.0"
        
        return ' '.join(parts)
    
    def modify_platform(self, base_platform: str) -> str:
        """Modify platform string"""
        variations = {
            'Win32': ['Win32', 'Win64', 'Windows'],
            'MacIntel': ['MacIntel', 'MacPPC', 'Mac68K'],
            'Linux x86_64': ['Linux x86_64', 'Linux i686', 'Linux armv71'],
            'iPhone': ['iPhone', 'iPod', 'iPad']
        }
        
        for key, values in variations.items():
            if key in base_platform:
                return random.choice(values)
        
        return base_platform
    
    def generate_canvas_fingerprint(self) -> Dict:
        """Generate canvas fingerprint"""
        pattern = random.choice(self.canvas_patterns)
        
        # Generate canvas data hash
        canvas_data = {
            'pattern': pattern,
            'width': random.randint(200, 400),
            'height': random.randint(100, 200),
            'opacity': random.uniform(0.8, 1.0),
            'compositeOperation': random.choice(['source-over', 'lighter', 'multiply']),
            'text': f"CanvasFingerprint{random.randint(1000, 9999)}",
            'font': random.choice(['Arial', 'Times New Roman', 'Courier New']),
            'fontSize': random.randint(12, 24),
            'textColor': f"rgba({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)},{random.uniform(0.5,1.0)})",
            'gradientStops': random.randint(2, 5),
            'shadowBlur': random.randint(0, 10),
            'lineWidth': random.uniform(0.5, 3.0)
        }
        
        # Calculate canvas hash
        canvas_string = json.dumps(canvas_data, sort_keys=True)
        canvas_hash = hashlib.md5(canvas_string.encode()).hexdigest()
        
        return {
            'data': canvas_data,
            'hash': canvas_hash,
            'winding': random.choice([True, False]),
            'textMetrics': {
                'width': random.randint(50, 200),
                'actualBoundingBoxLeft': random.randint(0, 10),
                'actualBoundingBoxRight': random.randint(10, 30)
            }
        }
    
    def generate_webgl_fingerprint(self) -> Dict:
        """Generate WebGL fingerprint"""
        renderer = random.choice(self.webgl_renderers)
        vendor = renderer.split(' ')[0]
        
        webgl_data = {
            'renderer': renderer,
            'vendor': vendor,
            'version': f"WebGL {random.choice(['1.0', '2.0'])}",
            'shadingLanguageVersion': f"WebGL GLSL ES {random.choice(['1.0', '3.0'])}",
            'maxTextureSize': random.choice([16384, 8192, 4096]),
            'maxCubeMapTextureSize': random.choice([16384, 8192, 4096]),
            'maxRenderBufferSize': random.choice([16384, 8192, 4096]),
            'maxViewportDims': [random.randint(8192, 16384), random.randint(8192, 16384)],
            'aliasedLineWidthRange': [1, random.randint(1, 10)],
            'aliasedPointSizeRange': [1, random.randint(1, 100)],
            'maxVertexAttribs': random.choice([16, 32, 64]),
            'maxVertexUniformVectors': random.choice([4096, 8192, 16384]),
            'maxFragmentUniformVectors': random.choice([4096, 8192, 16384]),
            'maxVaryingVectors': random.choice([8, 16, 32]),
            'supportsFloatTextures': random.choice([True, False]),
            'supportsHalfFloatTextures': random.choice([True, False])
        }
        
        # Calculate WebGL hash
        webgl_string = json.dumps(webgl_data, sort_keys=True)
        webgl_hash = hashlib.sha256(webgl_string.encode()).hexdigest()
        
        return {
            'data': webgl_data,
            'hash': webgl_hash,
            'unmaskedVendor': vendor,
            'unmaskedRenderer': renderer.split('(')[-1].split(')')[0] if '(' in renderer else renderer
        }
    
    def generate_audio_fingerprint(self) -> Dict:
        """Generate audio context fingerprint"""
        audio_data = {
            'sampleRate': random.choice([44100, 48000, 96000]),
            'channelCount': random.choice([1, 2, 6]),
            'channelCountMode': random.choice(['explicit', 'max', 'clamped-max']),
            'channelInterpretation': random.choice(['speakers', 'discrete']),
            'maxChannelCount': random.choice([2, 6, 8]),
            'numberOfInputs': random.randint(1, 8),
            'numberOfOutputs': random.randint(1, 8),
            'contextLatency': random.uniform(0.01, 0.1),
            'contextState': random.choice(['running', 'suspended', 'closed']),
            'nodes': random.sample(self.audio_contexts, k=random.randint(2, len(self.audio_contexts)))
        }
        
        # Generate audio buffer data
        audio_buffer = []
        for _ in range(random.randint(10, 50)):
            audio_buffer.append(random.uniform(-1.0, 1.0))
        
        audio_data['bufferData'] = audio_buffer[:10]  # First 10 values only
        
        # Calculate audio hash
        audio_string = json.dumps(audio_data, sort_keys=True)
        audio_hash = hashlib.sha1(audio_string.encode()).hexdigest()
        
        return {
            'data': audio_data,
            'hash': audio_hash,
            'dynamicsCompressor': {
                'threshold': random.uniform(-50, 0),
                'knee': random.uniform(0, 40),
                'ratio': random.uniform(1, 20),
                'attack': random.uniform(0.001, 0.1),
                'release': random.uniform(0.01, 1.0)
            }
        }
    
    def generate_font_fingerprint(self) -> Dict:
        """Generate font fingerprint"""
        font_families = [
            "Arial", "Helvetica", "Times New Roman", "Courier New",
            "Verdana", "Georgia", "Palatino", "Garamond",
            "Bookman", "Comic Sans MS", "Trebuchet MS", "Arial Black",
            "Impact", "Lucida Sans Unicode", "Tahoma", "Geneva"
        ]
        
        # Select random fonts
        selected_fonts = random.sample(font_families, k=random.randint(5, 10))
        
        font_data = {
            'families': selected_fonts,
            'availableFonts': len(selected_fonts),
            'monospace': random.choice(['monospace', 'Courier New', 'Lucida Console']),
            'serif': random.choice(['serif', 'Times New Roman', 'Georgia']),
            'sansSerif': random.choice(['sans-serif', 'Arial', 'Helvetica']),
            'cursive': random.choice(['cursive', 'Comic Sans MS', 'Brush Script MT']),
            'fantasy': random.choice(['fantasy', 'Impact', 'Papyrus']),
            'system': random.choice(['-apple-system', 'BlinkMacSystemFont', 'Segoe UI'])
        }
        
        # Calculate font hash
        font_string = json.dumps(font_data, sort_keys=True)
        font_hash = hashlib.md5(font_string.encode()).hexdigest()
        
        return {
            'data': font_data,
            'hash': font_hash,
            'fontMetrics': {
                'height': random.randint(16, 24),
                'ascent': random.randint(12, 20),
                'descent': random.randint(4, 8),
                'unitsPerEm': random.randint(1000, 2048)
            }
        }
    
    def generate_plugin_fingerprint(self) -> Dict:
        """Generate plugin fingerprint"""
        plugins = [
            {'name': 'Chrome PDF Viewer', 'filename': 'internal-pdf-viewer'},
            {'name': 'Chromium PDF Viewer', 'filename': 'internal-pdf-viewer'},
            {'name': 'Microsoft Edge PDF Viewer', 'filename': 'internal-pdf-viewer'},
            {'name': 'WebKit built-in PDF', 'filename': 'internal-pdf-viewer'},
            {'name': 'PDF Viewer', 'filename': 'mozilla-pdfjs'},
            {'name': 'Google Talk Plugin', 'filename': 'googletalk'},
            {'name': 'Google Talk Plugin Video Accelerator', 'filename': 'googletalk'},
            {'name': 'Java Deployment Toolkit', 'filename': 'npdeploytk'},
            {'name': 'Java(TM) Platform SE', 'filename': 'npjp2'},
            {'name': 'Silverlight Plug-In', 'filename': 'npctrl'},
            {'name': 'Windows Media Player Plug-in', 'filename': 'np-mswmp'},
            {'name': 'QuickTime Plug-in', 'filename': 'npqtplugin'},
            {'name': 'Adobe Acrobat', 'filename': 'nppdf32'},
            {'name': 'Shockwave Flash', 'filename': 'npswf32'}
        ]
        
        # Select random plugins
        selected_plugins = random.sample(plugins, k=random.randint(0, 5))
        
        plugin_data = {
            'plugins': selected_plugins,
            'pluginCount': len(selected_plugins),
            'mimeTypes': [],
            'enabledPlugin': random.choice([True, False])
        }
        
        # Add mime types for selected plugins
        mime_types = [
            'application/pdf',
            'application/x-google-chrome-pdf',
            'application/x-pdf',
            'text/pdf',
            'application/x-shockwave-flash',
            'application/futuresplash',
            'application/x-silverlight',
            'application/x-silverlight-2'
        ]
        
        plugin_data['mimeTypes'] = random.sample(mime_types, k=random.randint(0, 3))
        
        # Calculate plugin hash
        plugin_string = json.dumps(plugin_data, sort_keys=True)
        plugin_hash = hashlib.md5(plugin_string.encode()).hexdigest()
        
        return {
            'data': plugin_data,
            'hash': plugin_hash
        }
    
    def generate_time_fingerprint(self) -> Dict:
        """Generate time-based fingerprint"""
        import time
        from datetime import datetime
        
        current_time = time.time()
        
        time_data = {
            'timestamp': current_time,
            'performanceNow': random.uniform(0, 1000000),
            'timeOrigin': current_time - random.uniform(1000, 10000),
            'timezone': self.get_random_timezone(),
            'timezoneOffset': random.randint(-720, 720),  # -12 to +12 hours in minutes
            'clockDrift': random.uniform(-100, 100),  # milliseconds
            'clockResolution': random.choice([0.1, 0.5, 1.0, 5.0]),
            'dateString': datetime.fromtimestamp(current_time).strftime('%a %b %d %Y %H:%M:%S'),
            'dateUTCString': datetime.utcfromtimestamp(current_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
        
        # Calculate time hash
        time_string = json.dumps(time_data, sort_keys=True)
        time_hash = hashlib.sha256(time_string.encode()).hexdigest()
        
        return {
            'data': time_data,
            'hash': time_hash
        }
    
    def get_random_timezone(self) -> str:
        """Get random timezone"""
        timezones = [
            'America/New_York',
            'America/Los_Angeles',
            'America/Chicago',
            'America/Denver',
            'Europe/London',
            'Europe/Paris',
            'Europe/Berlin',
            'Asia/Tokyo',
            'Asia/Shanghai',
            'Asia/Kolkata',
            'Australia/Sydney',
            'Pacific/Auckland'
        ]
        
        return random.choice(timezones)
    
    def calculate_fingerprint_hash(self, fingerprint: Dict) -> str:
        """Calculate overall fingerprint hash"""
        # Create string representation
        fingerprint_string = json.dumps(fingerprint, sort_keys=True)
        
        # Calculate hash
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def apply_fingerprint_to_driver(self, driver, fingerprint: Dict):
        """Apply fingerprint to Selenium WebDriver"""
        try:
            # Apply basic fingerprint
            basic = fingerprint.get('basic', {})
            
            # Set user agent
            if 'userAgent' in basic:
                driver.execute_cdp_cmd(
                    'Network.setUserAgentOverride',
                    {'userAgent': basic['userAgent']}
                )
            
            # Set timezone
            if 'timezone' in basic:
                driver.execute_cdp_cmd(
                    'Emulation.setTimezoneOverride',
                    {'timezoneId': basic['timezone']}
                )
            
            # Set geolocation
            driver.execute_cdp_cmd(
                'Emulation.setGeolocationOverride',
                {
                    'latitude': random.uniform(-90, 90),
                    'longitude': random.uniform(-180, 180),
                    'accuracy': random.randint(10, 100)
                }
            )
            
            # Set other properties via JavaScript
            fingerprint_script = """
            // Override navigator properties
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => %d
            });
            
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => %d
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => '%s'
            });
            
            Object.defineProperty(navigator, 'language', {
                get: () => '%s'
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => %s
            });
            
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // Override screen properties
            Object.defineProperty(screen, 'width', {
                get: () => %d
            });
            
            Object.defineProperty(screen, 'height', {
                get: () => %d
            });
            
            Object.defineProperty(screen, 'colorDepth', {
                get: () => %d
            });
            
            Object.defineProperty(screen, 'pixelDepth', {
                get: () => %d
            });
            """ % (
                basic.get('hardwareConcurrency', 8),
                basic.get('deviceMemory', 8),
                basic.get('platform', 'Win32'),
                basic.get('language', 'en-US'),
                json.dumps(basic.get('languages', ['en-US', 'en'])),
                int(basic.get('screenResolution', '1920x1080').split('x')[0]),
                int(basic.get('screenResolution', '1920x1080').split('x')[1]),
                basic.get('colorDepth', 24),
                basic.get('pixelDepth', 24)
            )
            
            driver.execute_script(fingerprint_script)
            
            logger.debug(f"Applied fingerprint to driver: {fingerprint['hash'][:16]}...")
            
        except Exception as e:
            logger.error(f"Error applying fingerprint to driver: {e}")
    
    def generate_fingerprint_report(self, fingerprint: Dict) -> Dict:
        """Generate a report about the fingerprint"""
        report = {
            'fingerprint_hash': fingerprint.get('hash', ''),
            'uniqueness_score': self.calculate_uniqueness_score(fingerprint),
            'detection_risk': self.calculate_detection_risk(fingerprint),
            'components': {
                'basic': len(fingerprint.get('basic', {})),
                'canvas': bool(fingerprint.get('canvas', {}).get('hash')),
                'webgl': bool(fingerprint.get('webgl', {}).get('hash')),
                'audio': bool(fingerprint.get('audio', {}).get('hash')),
                'fonts': bool(fingerprint.get('fonts', {}).get('hash')),
                'plugins': bool(fingerprint.get('plugins', {}).get('hash')),
                'time': bool(fingerprint.get('time', {}).get('hash'))
            },
            'recommendations': []
        }
        
        # Add recommendations based on risk
        if report['detection_risk'] > 0.7:
            report['recommendations'].append("High detection risk - consider changing fingerprint")
        
        if not report['components']['canvas']:
            report['recommendations'].append("Add canvas fingerprint for better uniqueness")
        
        if not report['components']['webgl']:
            report['recommendations'].append("Add WebGL fingerprint for better uniqueness")
        
        return report
    
    def calculate_uniqueness_score(self, fingerprint: Dict) -> float:
        """Calculate uniqueness score (0-1)"""
        score = 0.0
        
        # Basic fingerprint (20%)
        if fingerprint.get('basic'):
            score += 0.2
        
        # Canvas fingerprint (20%)
        if fingerprint.get('canvas', {}).get('hash'):
            score += 0.2
        
        # WebGL fingerprint (20%)
        if fingerprint.get('webgl', {}).get('hash'):
            score += 0.2
        
        # Audio fingerprint (15%)
        if fingerprint.get('audio', {}).get('hash'):
            score += 0.15
        
        # Font fingerprint (15%)
        if fingerprint.get('fonts', {}).get('hash'):
            score += 0.15
        
        # Plugin fingerprint (5%)
        if fingerprint.get('plugins', {}).get('hash'):
            score += 0.05
        
        # Time fingerprint (5%)
        if fingerprint.get('time', {}).get('hash'):
            score += 0.05
        
        return min(1.0, score)
    
    def calculate_detection_risk(self, fingerprint: Dict) -> float:
        """Calculate detection risk (0-1)"""
        risk = 0.0
        
        basic = fingerprint.get('basic', {})
        
        # Check for inconsistencies
        if basic.get('webdriver') is True:
            risk += 0.3
        
        if basic.get('doNotTrack') is not None:
            risk += 0.1
        
        # Check for perfect round numbers (suspicious)
        if basic.get('hardwareConcurrency', 0) in [2, 4, 8, 16, 32]:
            risk += 0.05
        
        if basic.get('deviceMemory', 0) in [2, 4, 8, 16, 32]:
            risk += 0.05
        
        # Check screen resolution (common resolutions are less risky)
        common_resolutions = ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720']
        if basic.get('screenResolution') not in common_resolutions:
            risk += 0.1
        
        # Check for too many plugins (suspicious)
        plugin_count = fingerprint.get('plugins', {}).get('data', {}).get('pluginCount', 0)
        if plugin_count > 5:
            risk += 0.1
        
        return min(1.0, risk)