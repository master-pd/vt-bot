#!/usr/bin/env python3
"""
VT BOT SETUP - Auto Installation and Setup
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class VTSetup:
    """VT Bot Auto Setup System"""
    
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'CYAN': '\033[96m',
        'WHITE': '\033[97m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m',
        'RESET': '\033[0m'
    }
    
    def __init__(self):
        self.system = platform.system()
        self.project_dir = Path(__file__).parent
        self.python_version = (3, 12)
        
    def color(self, text, color):
        """Add color to text"""
        return f"{self.COLORS.get(color.upper(), '')}{text}{self.COLORS['RESET']}"
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if self.system == 'Windows' else 'clear')
    
    def print_banner(self):
        """Print setup banner"""
        banner = """
        ╔══════════════════════════════════════════════════════════╗
        ║                                                          ║
        ║        ██╗   ██╗████████╗    ██████╗  ██████╗ ████████╗ ║
        ║        ██║   ██║╚══██╔══╝    ██╔══██╗██╔═══██╗╚══██╔══╝ ║
        ║        ██║   ██║   ██║       ██████╔╝██║   ██║   ██║    ║
        ║        ██║   ██║   ██║       ██╔══██╗██║   ██║   ██║    ║
        ║        ╚██████╔╝   ██║       ██████╔╝╚██████╔╝   ██║    ║
        ║         ╚═════╝    ╚═╝       ╚═════╝  ╚═════╝    ╚═╝    ║
        ║                                                          ║
        ╠══════════════════════════════════════════════════════════╣
        ║               AUTO SETUP & INSTALLATION                  ║
        ║                  Version 4.0.0 - 2024                    ║
        ╚══════════════════════════════════════════════════════════╝
        """
        print(self.color(banner, 'CYAN'))
    
    def check_python(self):
        """Check Python version"""
        print(self.color("[1/8] Checking Python version...", "BLUE"))
        
        try:
            version = sys.version_info
            print(f"  Found Python {version.major}.{version.minor}.{version.micro}")
            
            if version.major == self.python_version[0] and version.minor >= self.python_version[1]:
                print(self.color("  ✓ Python version is compatible", "GREEN"))
                return True
            else:
                print(self.color(f"  ✗ Python {self.python_version[0]}.{self.python_version[1]}+ required", "RED"))
                return False
                
        except Exception as e:
            print(self.color(f"  ✗ Error checking Python: {e}", "RED"))
            return False
    
    def check_pip(self):
        """Check pip installation"""
        print(self.color("\n[2/8] Checking pip...", "BLUE"))
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', '--version'], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(self.color("  ✓ pip is installed", "GREEN"))
            return True
        except subprocess.CalledProcessError:
            print(self.color("  ✗ pip is not installed", "RED"))
            return False
    
    def create_virtualenv(self):
        """Create virtual environment"""
        print(self.color("\n[3/8] Creating virtual environment...", "BLUE"))
        
        venv_dir = self.project_dir / 'venv'
        
        if venv_dir.exists():
            print(self.color("  Virtual environment already exists", "YELLOW"))
            return True
        
        try:
            subprocess.check_call([sys.executable, '-m', 'venv', str(venv_dir)])
            print(self.color("  ✓ Virtual environment created", "GREEN"))
            return True
        except Exception as e:
            print(self.color(f"  ✗ Failed to create virtual environment: {e}", "RED"))
            return False
    
    def get_pip_path(self):
        """Get pip path for virtual environment"""
        if self.system == 'Windows':
            return self.project_dir / 'venv' / 'Scripts' / 'pip.exe'
        else:
            return self.project_dir / 'venv' / 'bin' / 'pip'
    
    def get_python_path(self):
        """Get Python path for virtual environment"""
        if self.system == 'Windows':
            return self.project_dir / 'venv' / 'Scripts' / 'python.exe'
        else:
            return self.project_dir / 'venv' / 'bin' / 'python'
    
    def install_dependencies(self):
        """Install Python dependencies"""
        print(self.color("\n[4/8] Installing dependencies...", "BLUE"))
        
        requirements_file = self.project_dir / 'requirements.txt'
        
        if not requirements_file.exists():
            print(self.color("  ✗ requirements.txt not found", "RED"))
            return False
        
        pip_path = self.get_pip_path()
        
        try:
            print("  Installing packages (this may take a few minutes)...")
            subprocess.check_call([str(pip_path), 'install', '-r', str(requirements_file)])
            print(self.color("  ✓ Dependencies installed successfully", "GREEN"))
            return True
        except subprocess.CalledProcessError as e:
            print(self.color(f"  ✗ Failed to install dependencies: {e}", "RED"))
            return False
        except Exception as e:
            print(self.color(f"  ✗ Error: {e}", "RED"))
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        print(self.color("\n[5/8] Creating directories...", "BLUE"))
        
        directories = [
            'data',
            'data/accounts',
            'data/proxies',
            'data/sessions',
            'data/logs',
            'data/config',
            'data/cache',
            'data/analytics',
            'data/backups',
            'assets',
            'assets/banners'
        ]
        
        try:
            for directory in directories:
                dir_path = self.project_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  Created: {directory}")
            
            print(self.color("  ✓ Directories created", "GREEN"))
            return True
        except Exception as e:
            print(self.color(f"  ✗ Failed to create directories: {e}", "RED"))
            return False
    
    def create_config_files(self):
        """Create default configuration files"""
        print(self.color("\n[6/8] Creating configuration files...", "BLUE"))
        
        try:
            # Create default accounts file
            accounts_file = self.project_dir / 'data' / 'accounts' / 'active_accounts.json'
            if not accounts_file.exists():
                with open(accounts_file, 'w', encoding='utf-8') as f:
                    f.write('[]')
            
            # Create default proxies file
            proxies_file = self.project_dir / 'data' / 'proxies' / 'proxy_list.json'
            if not proxies_file.exists():
                with open(proxies_file, 'w', encoding='utf-8') as f:
                    f.write('[]')
            
            # Create default settings file
            settings_file = self.project_dir / 'data' / 'config' / 'settings.json'
            if not settings_file.exists():
                default_settings = {
                    "system": {
                        "name": "VT Bot Ultra Pro",
                        "version": "4.0.0",
                        "author": "MASTER (RANA)",
                        "team": "MAR PD",
                        "environment": "production",
                        "debug": False,
                        "log_level": "INFO"
                    },
                    "performance": {
                        "max_concurrent_tasks": 50,
                        "max_views_per_minute": 10000,
                        "request_timeout": 30,
                        "retry_attempts": 3,
                        "retry_delay": 5,
                        "batch_size": 100,
                        "queue_size": 1000
                    },
                    "tiktok": {
                        "base_url": "https://www.tiktok.com",
                        "api_url": "https://api.tiktok.com",
                        "video_patterns": [
                            "https?://(www\\.|vm\\.|vt\\.)?tiktok\\.com/@[\\w.-]+/video/\\d+",
                            "https?://(www\\.)?tiktok\\.com/t/[\\w-]+",
                            "https?://(www\\.)?tiktok\\.com/[\\w-]+"
                        ],
                        "min_views": 1,
                        "max_views": 100000,
                        "default_views": 1000
                    },
                    "security": {
                        "protect_local_ip": True,
                        "use_proxy_rotation": True,
                        "proxy_timeout": 10,
                        "session_rotation": True,
                        "session_lifetime": 3600,
                        "cookie_rotation": True,
                        "user_agent_rotation": True
                    },
                    "anti_detection": {
                        "random_delays": True,
                        "min_delay": 1,
                        "max_delay": 5,
                        "human_like_behavior": True,
                        "mouse_movements": True,
                        "scroll_randomization": True,
                        "time_spent_variance": True,
                        "referrer_spoofing": True
                    }
                }
                
                import json
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
            
            print(self.color("  ✓ Configuration files created", "GREEN"))
            return True
        except Exception as e:
            print(self.color(f"  ✗ Failed to create config files: {e}", "RED"))
            return False
    
    def create_user_agents_file(self):
        """Create user agents file"""
        print(self.color("\n[7/8] Creating user agents file...", "BLUE"))
        
        user_agents = [
            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Chrome macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            # Mobile
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 14; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36"
        ]
        
        try:
            ua_file = self.project_dir / 'assets' / 'user_agents.txt'
            with open(ua_file, 'w', encoding='utf-8') as f:
                for ua in user_agents:
                    f.write(ua + '\n')
            
            print(self.color("  ✓ User agents file created", "GREEN"))
            return True
        except Exception as e:
            print(self.color(f"  ✗ Failed to create user agents file: {e}", "RED"))
            return False
    
    def create_launcher_scripts(self):
        """Create launcher scripts"""
        print(self.color("\n[8/8] Creating launcher scripts...", "BLUE"))
        
        try:
            # Create run script for Linux/Mac
            if self.system != 'Windows':
                run_script = self.project_dir / 'run.sh'
                with open(run_script, 'w') as f:
                    f.write('#!/bin/bash\n')
                    f.write('cd "$(dirname "$0")"\n')
                    f.write('source venv/bin/activate\n')
                    f.write('python vt_bot.py\n')
                
                os.chmod(run_script, 0o755)
                print("  Created: run.sh")
            
            # Create run script for Windows
            run_bat = self.project_dir / 'run.bat'
            with open(run_bat, 'w') as f:
                f.write('@echo off\n')
                f.write('cd /d "%~dp0"\n')
                f.write('call venv\\Scripts\\activate.bat\n')
                f.write('python vt_bot.py\n')
                f.write('pause\n')
            
            print("  Created: run.bat")
            
            print(self.color("  ✓ Launcher scripts created", "GREEN"))
            return True
        except Exception as e:
            print(self.color(f"  ✗ Failed to create launcher scripts: {e}", "RED"))
            return False
    
    def show_completion(self):
        """Show completion message"""
        print("\n" + "="*60)
        print(self.color("✅ SETUP COMPLETE!", "GREEN"))
        print("="*60)
        
        python_path = self.get_python_path()
        
        print("\n" + self.color("Next Steps:", "BOLD"))
        print("1. Add your TikTok accounts to: data/accounts/active_accounts.json")
        print("2. Add proxies to: data/proxies/proxy_list.json")
        print("3. Configure settings in: data/config/settings.json")
        print("\n" + self.color("To start VT Bot:", "BOLD"))
        
        if self.system == 'Windows':
            print("  Double-click 'run.bat' or run:")
            print(f"  {python_path} vt_bot.py")
        else:
            print("  Run: ./run.sh")
            print("  Or:")
            print(f"  {python_path} vt_bot.py")
        
        print("\n" + self.color("Important Notes:", "YELLOW"))
        print("• Use only dummy/old accounts")
        print("• Real accounts may get banned")
        print("• For educational purposes only")
        print("• Follow local laws and regulations")
        
        print("\n" + self.color("📚 Documentation:", "CYAN"))
        print("• Check README.md for detailed instructions")
        print("• Use '--help' flag for command line options")
        
        print("\n" + self.color("👨‍💻 Author: MASTER (RANA)", "MAGENTA"))
        print(self.color("👥 Team: MAR PD", "MAGENTA"))
        print("\n")
    
    def run_setup(self):
        """Run complete setup process"""
        self.clear_screen()
        self.print_banner()
        
        print(self.color("Starting VT Bot Auto Setup...", "BOLD"))
        print("="*60 + "\n")
        
        # Run all setup steps
        steps = [
            ("Python Check", self.check_python),
            ("PIP Check", self.check_pip),
            ("Virtual Environment", self.create_virtualenv),
            ("Dependencies", self.install_dependencies),
            ("Directories", self.create_directories),
            ("Config Files", self.create_config_files),
            ("User Agents", self.create_user_agents_file),
            ("Launcher Scripts", self.create_launcher_scripts)
        ]
        
        failed_steps = []
        
        for step_name, step_func in steps:
            try:
                success = step_func()
                if not success:
                    failed_steps.append(step_name)
            except Exception as e:
                print(self.color(f"  ✗ Error in {step_name}: {e}", "RED"))
                failed_steps.append(step_name)
        
        if failed_steps:
            print("\n" + self.color("❌ SETUP FAILED!", "RED"))
            print(self.color("Failed steps:", "YELLOW"))
            for step in failed_steps:
                print(f"  • {step}")
            print("\nPlease fix the issues and run setup again.")
            return False
        else:
            self.show_completion()
            return True

def main():
    """Main function"""
    try:
        setup = VTSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n" + VTSetup().color("Setup cancelled by user", "YELLOW"))
        sys.exit(1)
    except Exception as e:
        print("\n" + VTSetup().color(f"Unexpected error: {e}", "RED"))
        sys.exit(1)

if __name__ == "__main__":
    main()