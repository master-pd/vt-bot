"""
Method 5: Puppeteer/Playwright - Node.js browser automation
"""

import os
import subprocess
import json
import tempfile
import time
import random
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PuppeteerMethod:
    def __init__(self):
        self.name = "puppeteer"
        self.success_rate = 80  # 80% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Check Node.js availability
        self.node_available = self.check_node_js()
        self.script_dir = "scripts/puppeteer"
        
        # Create script directory
        os.makedirs(self.script_dir, exist_ok=True)
    
    def check_node_js(self) -> bool:
        """Check if Node.js is installed"""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def is_available(self) -> bool:
        """Check if Puppeteer method is available"""
        if not self.node_available:
            logger.warning("Node.js is not installed")
            return False
        
        # Check if puppeteer is installed
        try:
            result = subprocess.run(
                ['npm', 'list', 'puppeteer'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.script_dir
            )
            return 'puppeteer' in result.stdout
        except:
            # Try to install puppeteer
            return self.install_puppeteer()
    
    def install_puppeteer(self) -> bool:
        """Install Puppeteer"""
        try:
            logger.info("Installing Puppeteer...")
            
            # Create package.json if not exists
            package_json = {
                "name": "tiktok-viewer-puppeteer",
                "version": "1.0.0",
                "dependencies": {
                    "puppeteer": "^21.0.0",
                    "puppeteer-extra": "^3.3.6",
                    "puppeteer-extra-plugin-stealth": "^2.11.2"
                }
            }
            
            with open(os.path.join(self.script_dir, 'package.json'), 'w') as f:
                json.dump(package_json, f, indent=2)
            
            # Install dependencies
            result = subprocess.run(
                ['npm', 'install'],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.script_dir
            )
            
            if result.returncode == 0:
                logger.info("Puppeteer installed successfully")
                return True
            else:
                logger.error(f"Failed to install Puppeteer: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing Puppeteer: {e}")
            return False
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using Puppeteer"""
        logger.info(f"Puppeteer Method: Sending {view_count} views")
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0
        }
        
        # Create Puppeteer script
        script_content = self.generate_puppeteer_script(video_url, view_count)
        
        # Save script to file
        script_file = os.path.join(self.script_dir, 'send_views.js')
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        try:
            # Run Puppeteer script
            logger.info("Running Puppeteer script...")
            
            result = subprocess.run(
                ['node', script_file],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                cwd=self.script_dir
            )
            
            if result.returncode == 0:
                # Parse results from output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'SUCCESS:' in line:
                        results['success_count'] = int(line.split(':')[1].strip())
                    elif 'FAILED:' in line:
                        results['failed_count'] = int(line.split(':')[1].strip())
                
                logger.debug(f"Puppeteer output: {result.stdout}")
            else:
                logger.error(f"Puppeteer script failed: {result.stderr}")
                results['failed_count'] = view_count
        
        except subprocess.TimeoutExpired:
            logger.error("Puppeteer script timed out")
            results['failed_count'] = view_count
        except Exception as e:
            logger.error(f"Error running Puppeteer: {e}")
            results['failed_count'] = view_count
        
        # Update statistics
        self.total_views_sent += view_count
        self.successful_views += results['success_count']
        self.last_used = time.time()
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"Puppeteer Results: {results['success_count']}/{view_count} successful")
        return results
    
    def generate_puppeteer_script(self, video_url: str, view_count: int) -> str:
        """Generate Puppeteer JavaScript script"""
        return f"""
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const {{ executablePath }} = require('puppeteer');

// Use stealth plugin
puppeteer.use(StealthPlugin());

async function sendTikTokViews() {{
    let successCount = 0;
    let failedCount = 0;
    const videoUrl = '{video_url}';
    const totalViews = {view_count};
    
    console.log('Starting Puppeteer TikTok Viewer...');
    console.log(`Target URL: ${{videoUrl}}`);
    console.log(`Views to send: ${{totalViews}}`);
    
    for (let i = 0; i < totalViews; i++) {{
        try {{
            console.log(`\\n[View ${{i+1}}/${{totalViews}}] Starting...`);
            
            // Launch browser with stealth settings
            const browser = await puppeteer.launch({{
                headless: Math.random() > 0.5, // Random headless
                executablePath: executablePath(),
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-blink-features=AutomationControlled',
                    `--window-size=${{Math.floor(Math.random() * 400) + 1200}},${{Math.floor(Math.random() * 400) + 800}}`,
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding'
                ],
                ignoreHTTPSErrors: true
            }});
            
            const page = await browser.newPage();
            
            // Set random user agent
            const userAgents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
                'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
            ];
            
            const randomUA = userAgents[Math.floor(Math.random() * userAgents.length)];
            await page.setUserAgent(randomUA);
            
            // Set extra headers
            await page.setExtraHTTPHeaders({{
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.tiktok.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }});
            
            // Navigate to video
            console.log('Navigating to video...');
            await page.goto(videoUrl, {{
                waitUntil: 'networkidle2',
                timeout: 30000
            }});
            
            // Wait for video element
            console.log('Waiting for video...');
            await page.waitForSelector('video', {{ timeout: 10000 }});
            
            // Simulate human behavior
            console.log('Simulating human behavior...');
            
            // Random mouse movements
            for (let j = 0; j < 5; j++) {{
                const x = Math.floor(Math.random() * 800) + 100;
                const y = Math.floor(Math.random() * 600) + 100;
                await page.mouse.move(x, y);
                await page.waitForTimeout(Math.random() * 500 + 100);
            }}
            
            // Random scrolls
            for (let j = 0; j < 3; j++) {{
                const scrollAmount = Math.floor(Math.random() * 400) + 100;
                await page.evaluate((amount) => {{
                    window.scrollBy(0, amount);
                }}, scrollAmount);
                await page.waitForTimeout(Math.random() * 1000 + 500);
            }}
            
            // Watch video
            const watchTime = Math.floor(Math.random() * 30) + 15;
            console.log(`Watching video for ${{watchTime}} seconds...`);
            
            for (let j = 0; j < watchTime; j++) {{
                // Random interactions during watch
                if (Math.random() < 0.1) {{
                    const scrollAmount = Math.floor(Math.random() * 200) - 100;
                    await page.evaluate((amount) => {{
                        window.scrollBy(0, amount);
                    }}, scrollAmount);
                }}
                
                await page.waitForTimeout(1000);
            }}
            
            // Random like (30% chance)
            if (Math.random() < 0.3) {{
                console.log('Attempting to like video...');
                try {{
                    await page.evaluate(() => {{
                        const likeButtons = document.querySelectorAll('[data-e2e="like-icon"], button[aria-label*="Like"]');
                        if (likeButtons.length > 0) {{
                            likeButtons[0].click();
                        }}
                    }});
                    await page.waitForTimeout(1000);
                }} catch (e) {{
                    // Ignore like errors
                }}
            }}
            
            // Wait a bit more
            await page.waitForTimeout(Math.random() * 3000 + 1000);
            
            // Close browser
            await browser.close();
            
            successCount++;
            console.log(`[View ${{i+1}}] SUCCESS`);
            
            // Delay between views
            if (i < totalViews - 1) {{
                const delay = Math.floor(Math.random() * 5000) + 2000;
                console.log(`Waiting ${{delay/1000}} seconds before next view...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }}
            
        }} catch (error) {{
            console.error(`[View ${{i+1}}] FAILED: ${{error.message}}`);
            failedCount++;
            
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 3000));
        }}
    }}
    
    console.log('\\n========== FINAL RESULTS ==========');
    console.log(`SUCCESS: ${{successCount}}`);
    console.log(`FAILED: ${{failedCount}}`);
    console.log(`SUCCESS RATE: ${{(successCount/totalViews*100).toFixed(1)}}%`);
    console.log('===================================');
    
    return {{ success: successCount, failed: failedCount }};
}}

// Run the function
sendTikTokViews().catch(console.error);
"""
    
    def send_single_view(self, video_url: str) -> bool:
        """Send single view using Puppeteer"""
        # Create simple script for single view
        script = self.generate_single_view_script(video_url)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script)
            temp_file = f.name
        
        try:
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.script_dir
            )
            
            os.unlink(temp_file)
            
            return result.returncode == 0 and 'SUCCESS' in result.stdout
            
        except:
            try:
                os.unlink(temp_file)
            except:
                pass
            return False
    
    def generate_single_view_script(self, video_url: str) -> str:
        """Generate single view Puppeteer script"""
        return f"""
const puppeteer = require('puppeteer');

(async () => {{
    try {{
        const browser = await puppeteer.launch({{ headless: true }});
        const page = await browser.newPage();
        
        await page.goto('{video_url}', {{ waitUntil: 'networkidle2' }});
        await page.waitForSelector('video');
        
        // Watch for 15-30 seconds
        const watchTime = Math.floor(Math.random() * 15) + 15;
        await page.waitForTimeout(watchTime * 1000);
        
        await browser.close();
        console.log('SUCCESS');
    }} catch (error) {{
        console.error('FAILED:', error.message);
        process.exit(1);
    }}
}})();
"""
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup method"""
        # Cleanup temporary files
        try:
            temp_files = [f for f in os.listdir(self.script_dir) if f.endswith('.js')]
            for file in temp_files:
                if file not in ['package.json', 'package-lock.json']:
                    os.remove(os.path.join(self.script_dir, file))
        except:
            pass