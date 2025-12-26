#!/usr/bin/env python3
"""
VT Bot Launcher - System Startup
"""

import os
import sys
import platform
import subprocess
import time
from pathlib import Path

class VTLauncher:
    """VT Bot System Launcher"""
    
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'end': '\033[0m'
    }
    
    def __init__(self):
        self.system = platform.system()
        self.project_dir = Path(__file__).parent
        self.is_setup = False
        
    def color_text(self, text, color):
        """Add color to text"""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['end']}"
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if self.system == 'Windows' else 'clear')
    
    def show_header(self):
        """Show launcher header"""
        self.clear_screen()
        header = f"""
        {self.color_text('╔══════════════════════════════════════════════════════════╗', 'cyan')}
        {self.color_text('║', 'cyan')}      {self.color_text('🎯 VT BOT ULTRA PRO LAUNCHER 🚀', 'magenta')}          {self.color_text('║', 'cyan')}
        {self.color_text('╠══════════════════════════════════════════════════════════╣', 'cyan')}
        {self.color_text('║', 'cyan')}   Author: {self.color_text('MASTER (RANA)', 'green')}                       {self.color_text('║', 'cyan')}
        {self.color_text('║', 'cyan')}   Team: {self.color_text('MAR PD', 'yellow')}                             {self.color_text('║', 'cyan')}
        {self.color_text('║', 'cyan')}   Version: {self.color_text('4.0.0', 'blue')}                            {self.color_text('║', 'cyan')}
        {self.color_text('║', 'cyan')}   Platform: {self.color_text(self.system, 'yellow')}                        {self.color_text('║', 'cyan')}
        {self.color_text('╚══════════════════════════════════════════════════════════╝', 'cyan')}
        
        {self.color_text('[SYSTEM CHECK]', 'bold')}
        """
        print(header)
    
    def check_python(self):
        """Check Python version"""
        try:
            version = sys.version_info
            if version.major == 3 and version.minor >= 9:
                print(f"{self.color_text('✓', 'green')} Python {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                print(f"{self.color_text('✗', 'red')} Python 3.9+ required (Found {version.major}.{version.minor})")
                return False
        except:
            print(f"{self.color_text('✗', 'red')} Python check failed")
            return False
    
    def check_dependencies(self):
        """Check required dependencies"""
        print(f"\n{self.color_text('[DEPENDENCIES]', 'bold')}")
        
        required = ['aiohttp', 'requests', 'colorama']
        all_ok = True
        
        for dep in required:
            try:
                __import__(dep)
                print(f"{self.color_text('✓', 'green')} {dep}")
            except ImportError:
                print(f"{self.color_text('✗', 'red')} {dep}")
                all_ok = False
        
        return all_ok
    
    def check_directories(self):
        """Check and create directories"""
        print(f"\n{self.color_text('[DIRECTORIES]', 'bold')}")
        
        dirs = [
            self.project_dir / 'data',
            self.project_dir / 'data/accounts',
            self.project_dir / 'data/proxies',
            self.project_dir / 'data/sessions',
            self.project_dir / 'data/logs',
            self.project_dir / 'data/config',
            self.project_dir / 'data/cache',
            self.project_dir / 'assets',
            self.project_dir / 'assets/banners'
        ]
        
        for dir_path in dirs:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"{self.color_text('✓', 'green')} {dir_path.relative_to(self.project_dir)}")
            except Exception as e:
                print(f"{self.color_text('✗', 'red')} {dir_path.relative_to(self.project_dir)}: {e}")
    
    def install_requirements(self):
        """Install Python requirements"""
        print(f"\n{self.color_text('[INSTALLATION]', 'bold')}")
        
        req_file = self.project_dir / 'requirements.txt'
        if not req_file.exists():
            print(f"{self.color_text('✗', 'red')} requirements.txt not found")
            return False
        
        try:
            print(f"{self.color_text('⏳', 'yellow')} Installing dependencies...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(req_file)])
            print(f"{self.color_text('✓', 'green')} Dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{self.color_text('✗', 'red')} Installation failed: {e}")
            return False
    
    def setup_environment(self):
        """Setup complete environment"""
        self.show_header()
        
        print(f"{self.color_text('⚙️  Setting up VT Bot environment...', 'cyan')}\n")
        
        # Check Python
        if not self.check_python():
            print(f"\n{self.color_text('❌ Python 3.9+ is required!', 'red')}")
            time.sleep(3)
            return False
        
        # Check dependencies
        if not self.check_dependencies():
            print(f"\n{self.color_text('⚠️  Some dependencies missing', 'yellow')}")
            choice = input(f"{self.color_text('Install missing dependencies? (y/n): ', 'cyan')}")
            if choice.lower() == 'y':
                if not self.install_requirements():
                    return False
        
        # Create directories
        self.check_directories()
        
        # Create config files if not exist
        self.create_default_configs()
        
        print(f"\n{self.color_text('✅ Environment setup complete!', 'green')}")
        time.sleep(2)
        self.is_setup = True
        return True
    
    def create_default_configs(self):
        """Create default configuration files"""
        config_files = {
            'data/accounts/active_accounts.json': '[]',
            'data/proxies/proxy_list.json': '[]',
            'data/config/settings.json': '{}',
            'data/config/runtime_config.json': '{}'
        }
        
        for file_path, default_content in config_files.items():
            full_path = self.project_dir / file_path
            if not full_path.exists():
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(default_content)
    
    def launch_bot(self):
        """Launch the main bot"""
        if not self.is_setup:
            if not self.setup_environment():
                print(f"\n{self.color_text('❌ Setup failed!', 'red')}")
                time.sleep(3)
                return
        
        self.clear_screen()
        
        # Show launch animation
        launch_text = """
        ╔══════════════════════════════════════════════════════════╗
        ║                 🚀 LAUNCHING VT BOT 🚀                   ║
        ║                                                          ║
        ║             Professional TikTok View System              ║
        ║                  Version 4.0.0 - Ultra Pro               ║
        ║                                                          ║
        ║                 Author: MASTER (RANA)                    ║
        ║                  Team: MAR PD                            ║
        ║                                                          ║
        ║        ████████╗ ███████╗ ████████╗████████╗███████╗    ║
        ║        ╚══██╔══╝██╔════╝ ╚══██╔══╝╚══██╔══╝██╔════╝    ║
        ║           ██║   █████╗      ██║      ██║   ███████╗    ║
        ║           ██║   ██╔══╝      ██║      ██║   ╚════██║    ║
        ║           ██║   ███████╗    ██║      ██║   ███████║    ║
        ║           ╚═╝   ╚══════╝    ╚═╝      ╚═╝   ╚══════╝    ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        """
        
        colored_launch = ""
        for line in launch_text.split('\n'):
            if '█' in line:
                colored_launch += self.color_text(line, 'cyan') + '\n'
            elif '╔' in line or '║' in line or '╚' in line or '╠' in line or '╣' in line:
                colored_launch += self.color_text(line, 'blue') + '\n'
            else:
                colored_launch += self.color_text(line, 'magenta') + '\n'
        
        print(colored_launch)
        time.sleep(2)
        
        # Launch the bot
        try:
            bot_path = self.project_dir / 'vt_bot.py'
            if bot_path.exists():
                print(f"\n{self.color_text('🚀 Starting VT Bot...', 'green')}")
                time.sleep(1)
                os.system(f'{sys.executable} {bot_path}')
            else:
                print(f"\n{self.color_text('❌ vt_bot.py not found!', 'red')}")
                time.sleep(3)
        except KeyboardInterrupt:
            print(f"\n{self.color_text('⚠️  Launch cancelled by user', 'yellow')}")
            time.sleep(2)
        except Exception as e:
            print(f"\n{self.color_text(f'❌ Launch error: {e}', 'red')}")
            time.sleep(3)
    
    def show_menu(self):
        """Show launcher menu"""
        while True:
            self.clear_screen()
            self.show_header()
            
            menu = f"""
        {self.color_text('[MAIN MENU]', 'bold')}
        
        {self.color_text('1.', 'cyan')} {self.color_text('🚀 Launch VT Bot', 'green')}
        {self.color_text('2.', 'cyan')} {self.color_text('⚙️  Setup Environment', 'yellow')}
        {self.color_text('3.', 'cyan')} {self.color_text('📊 Check System', 'blue')}
        {self.color_text('4.', 'cyan')} {self.color_text('🛠️  Install Dependencies', 'magenta')}
        {self.color_text('5.', 'cyan')} {self.color_text('📁 Open Data Folder', 'cyan')}
        {self.color_text('6.', 'cyan')} {self.color_text('❌ Exit', 'red')}
        
        {self.color_text('Select option (1-6):', 'bold')} """
        
            print(menu)
            
            try:
                choice = input().strip()
                
                if choice == '1':
                    self.launch_bot()
                elif choice == '2':
                    self.setup_environment()
                elif choice == '3':
                    self.show_header()
                    self.check_python()
                    self.check_dependencies()
                    self.check_directories()
                    input(f"\n{self.color_text('Press Enter to continue...', 'cyan')}")
                elif choice == '4':
                    self.install_requirements()
                    input(f"\n{self.color_text('Press Enter to continue...', 'cyan')}")
                elif choice == '5':
                    self.open_data_folder()
                elif choice == '6':
                    print(f"\n{self.color_text('👋 Goodbye!', 'green')}")
                    time.sleep(1)
                    break
                else:
                    print(f"\n{self.color_text('❌ Invalid choice!', 'red')}")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print(f"\n{self.color_text('👋 Goodbye!', 'green')}")
                time.sleep(1)
                break
    
    def open_data_folder(self):
        """Open data folder"""
        data_path = self.project_dir / 'data'
        try:
            if self.system == 'Windows':
                os.startfile(data_path)
            elif self.system == 'Darwin':  # macOS
                subprocess.call(['open', str(data_path)])
            else:  # Linux
                subprocess.call(['xdg-open', str(data_path)])
            print(f"\n{self.color_text('✅ Opened data folder', 'green')}")
        except Exception as e:
            print(f"\n{self.color_text(f'❌ Failed to open folder: {e}', 'red')}")
        time.sleep(2)

def main():
    """Main launcher function"""
    launcher = VTLauncher()
    launcher.show_menu()

if __name__ == "__main__":
    main()