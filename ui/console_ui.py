"""
Console UI for TikTok View Bot
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from colorama import init, Fore, Back, Style
import pyfiglet
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live

init(autoreset=True)
console = Console()
logger = logging.getLogger(__name__)

class ConsoleUI:
    def __init__(self):
        self.bot_status = "stopped"
        self.current_task = None
        self.stats = {}
        self.last_update = time.time()
        
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        """Show ASCII art banner"""
        self.clear_screen()
        
        banner = pyfiglet.figlet_format("TikTok Bot", font="slant")
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + banner)
        print(Fore.CYAN + "=" * 70)
        print(Fore.YELLOW + "Advanced TikTok View Automation System")
        print(Fore.CYAN + "Version 2.5 | Developer: Anonymous")
        print(Fore.CYAN + "=" * 70)
        print()
    
    def show_main_menu(self):
        """Show main menu"""
        self.show_banner()
        
        menu_options = [
            f"{Fore.GREEN}[1]{Fore.WHITE} Start Bot",
            f"{Fore.GREEN}[2]{Fore.WHITE} Stop Bot",
            f"{Fore.GREEN}[3]{Fore.WHITE} Send Views",
            f"{Fore.GREEN}[4]{Fore.WHITE} Check Status",
            f"{Fore.GREEN}[5]{Fore.WHITE} View Statistics",
            f"{Fore.GREEN}[6]{Fore.WHITE} Proxy Manager",
            f"{Fore.GREEN}[7]{Fore.WHITE} Account Manager",
            f"{Fore.GREEN}[8]{Fore.WHITE} Settings",
            f"{Fore.GREEN}[9]{Fore.WHITE} Help",
            f"{Fore.RED}[0]{Fore.WHITE} Exit"
        ]
        
        print(Fore.CYAN + "MAIN MENU")
        print(Fore.CYAN + "-" * 30)
        
        for option in menu_options:
            print(f"  {option}")
        
        print()
        print(Fore.CYAN + "-" * 30)
        
        choice = input(Fore.YELLOW + "Select option [0-9]: " + Fore.WHITE)
        return choice
    
    def show_status_dashboard(self, bot_data: Dict):
        """Show real-time status dashboard"""
        with Live(auto_refresh=False) as live:
            while True:
                layout = self.create_dashboard_layout(bot_data)
                live.update(layout)
                live.refresh()
                
                # Update every 2 seconds
                time.sleep(2)
                
                # Check for exit
                if self.check_keypress():
                    break
    
    def create_dashboard_layout(self, bot_data: Dict) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        
        # Split into sections
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        header_text = f"🚀 TikTok View Bot Pro - {datetime.now().strftime('%H:%M:%S')}"
        layout["header"].update(
            Panel(header_text, style="bold cyan")
        )
        
        # Main content - split into columns
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        # Left panel - Status
        status_table = Table(title="Bot Status", show_header=True, header_style="bold magenta")
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Value", style="green")
        
        status_table.add_row("Bot Status", bot_data.get('status', 'Unknown'))
        status_table.add_row("Active Tasks", str(bot_data.get('active_tasks', 0)))
        status_table.add_row("Queue Size", str(bot_data.get('queue_size', 0)))
        status_table.add_row("Uptime", bot_data.get('uptime', '0s'))
        
        layout["left"].update(Panel(status_table))
        
        # Right panel - Quick Stats
        stats_table = Table(title="Quick Stats", show_header=True, header_style="bold yellow")
        stats_table.add_column("Stat", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Views", f"{bot_data.get('total_views', 0):,}")
        stats_table.add_row("Success Rate", f"{bot_data.get('success_rate', 0):.1f}%")
        stats_table.add_row("Proxies", str(bot_data.get('active_proxies', 0)))
        stats_table.add_row("Accounts", str(bot_data.get('active_accounts', 0)))
        
        layout["right"].update(Panel(stats_table))
        
        # Footer - Controls
        controls = (
            "[Q]uit  [S]tart  [P]ause  [R]efresh  [L]ogs"
        )
        layout["footer"].update(
            Panel(controls, style="bold white on blue")
        )
        
        return layout
    
    def show_send_views_menu(self):
        """Show menu for sending views"""
        self.clear_screen()
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "SEND VIEWS")
        print(Fore.CYAN + "=" * 70)
        print()
        
        # Get video URL
        video_url = input(Fore.YELLOW + "Enter TikTok Video URL: " + Fore.WHITE)
        
        if not video_url.startswith("http"):
            print(Fore.RED + "Invalid URL!")
            time.sleep(2)
            return
        
        # Get view count
        try:
            view_count = int(input(Fore.YELLOW + "Enter number of views: " + Fore.WHITE))
        except:
            print(Fore.RED + "Invalid number!")
            time.sleep(2)
            return
        
        # Select method
        print(Fore.CYAN + "\nAvailable Methods:")
        print(Fore.CYAN + "-" * 30)
        methods = [
            ("1", "Browser Automation", "Most reliable"),
            ("2", "API Direct", "Fast but less reliable"),
            ("3", "Multi-Account", "High success rate"),
            ("4", "Auto Select", "Let bot choose best")
        ]
        
        for method_id, method_name, description in methods:
            print(f"{Fore.GREEN}[{method_id}] {Fore.WHITE}{method_name:20} {Fore.CYAN}- {description}")
        
        method_choice = input(Fore.YELLOW + "\nSelect method [1-4]: " + Fore.WHITE)
        
        method_map = {
            "1": "browser",
            "2": "api",
            "3": "multi_account",
            "4": "auto"
        }
        
        method = method_map.get(method_choice, "auto")
        
        # Confirm
        print(Fore.CYAN + "\n" + "=" * 70)
        print(Fore.YELLOW + "CONFIRMATION")
        print(Fore.CYAN + "-" * 30)
        print(Fore.WHITE + f"Video URL: {video_url}")
        print(Fore.WHITE + f"Views: {view_count}")
        print(Fore.WHITE + f"Method: {method}")
        print(Fore.CYAN + "-" * 30)
        
        confirm = input(Fore.YELLOW + "Start sending views? [y/N]: " + Fore.WHITE)
        
        if confirm.lower() == 'y':
            return {
                'video_url': video_url,
                'view_count': view_count,
                'method': method
            }
        
        return None
    
    def show_progress_bar(self, task_id: str, total_views: int, completed_views: int):
        """Show progress bar for view sending"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[cyan]{task.completed}/{task.total} views"),
            console=console
        ) as progress:
            
            task = progress.add_task(
                f"[green]Sending views... Task: {task_id}",
                total=total_views
            )
            
            # Simulate progress updates
            # In real implementation, this would update from bot
            while not progress.finished:
                progress.update(task, completed=completed_views)
                time.sleep(0.5)
    
    def show_statistics(self, stats_data: Dict):
        """Show detailed statistics"""
        self.clear_screen()
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "📊 BOT STATISTICS")
        print(Fore.CYAN + "=" * 70)
        print()
        
        # Overall Stats
        print(Fore.YELLOW + "OVERALL STATISTICS")
        print(Fore.CYAN + "-" * 40)
        
        overall_stats = [
            ("Total Views Sent", stats_data.get('total_views_sent', 0)),
            ("Successful Views", stats_data.get('successful_views', 0)),
            ("Failed Views", stats_data.get('failed_views', 0)),
            ("Success Rate", f"{stats_data.get('success_rate', 0):.1f}%"),
            ("Total Tasks", stats_data.get('total_tasks', 0)),
            ("Uptime", stats_data.get('uptime', '0s'))
        ]
        
        for label, value in overall_stats:
            print(f"{Fore.CYAN}{label:25} {Fore.GREEN}{value}")
        
        print()
        
        # Method-wise Stats
        print(Fore.YELLOW + "METHOD PERFORMANCE")
        print(Fore.CYAN + "-" * 40)
        
        methods = stats_data.get('methods', {})
        for method_name, method_stats in methods.items():
            success_rate = method_stats.get('success_rate', 0)
            views_sent = method_stats.get('views_sent', 0)
            
            # Color code based on success rate
            if success_rate >= 80:
                color = Fore.GREEN
            elif success_rate >= 60:
                color = Fore.YELLOW
            else:
                color = Fore.RED
            
            print(f"{Fore.CYAN}{method_name:20} {color}{success_rate:6.1f}%  {Fore.WHITE}{views_sent:,} views")
        
        print()
        
        # Recent Tasks
        print(Fore.YELLOW + "RECENT TASKS")
        print(Fore.CYAN + "-" * 40)
        
        recent_tasks = stats_data.get('recent_tasks', [])
        for task in recent_tasks[:5]:  # Show last 5 tasks
            task_id = task.get('id', 'Unknown')[:8]
            status = task.get('status', 'Unknown')
            views = f"{task.get('completed', 0)}/{task.get('requested', 0)}"
            
            status_color = Fore.GREEN if status == 'completed' else Fore.RED
            print(f"{Fore.CYAN}{task_id:10} {status_color}{status:12} {Fore.WHITE}{views} views")
        
        print()
        input(Fore.YELLOW + "Press Enter to continue..." + Fore.WHITE)
    
    def show_proxy_manager(self, proxy_data: Dict):
        """Show proxy manager interface"""
        self.clear_screen()
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "🌐 PROXY MANAGER")
        print(Fore.CYAN + "=" * 70)
        print()
        
        # Proxy Statistics
        total_proxies = proxy_data.get('total', 0)
        active_proxies = proxy_data.get('active', 0)
        inactive_proxies = proxy_data.get('inactive', 0)
        
        print(Fore.YELLOW + "PROXY STATISTICS")
        print(Fore.CYAN + "-" * 40)
        print(f"{Fore.CYAN}Total Proxies:{Fore.GREEN:>25} {total_proxies}")
        print(f"{Fore.CYAN}Active Proxies:{Fore.GREEN:>24} {active_proxies}")
        print(f"{Fore.CYAN}Inactive Proxies:{Fore.RED:>22} {inactive_proxies}")
        
        if total_proxies > 0:
            active_percent = (active_proxies / total_proxies) * 100
            print(f"{Fore.CYAN}Active Rate:{Fore.GREEN:>27} {active_percent:.1f}%")
        
        print()
        
        # Proxy Actions
        print(Fore.YELLOW + "ACTIONS")
        print(Fore.CYAN + "-" * 40)
        
        actions = [
            ("1", "Refresh Proxies", "Fetch new proxies"),
            ("2", "Check All Proxies", "Validate all proxies"),
            ("3", "Export Proxies", "Save to file"),
            ("4", "Import Proxies", "Load from file"),
            ("5", "View Active Proxies", "Show list"),
            ("6", "Back to Main Menu", "Return")
        ]
        
        for action_id, action_name, description in actions:
            print(f"{Fore.GREEN}[{action_id}] {Fore.WHITE}{action_name:20} {Fore.CYAN}- {description}")
        
        print()
        choice = input(Fore.YELLOW + "Select action [1-6]: " + Fore.WHITE)
        return choice
    
    def show_account_manager(self, account_data: Dict):
        """Show account manager interface"""
        self.clear_screen()
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "👤 ACCOUNT MANAGER")
        print(Fore.CYAN + "=" * 70)
        print()
        
        # Account Statistics
        total_accounts = account_data.get('total', 0)
        active_accounts = account_data.get('active', 0)
        inactive_accounts = account_data.get('inactive', 0)
        
        print(Fore.YELLOW + "ACCOUNT STATISTICS")
        print(Fore.CYAN + "-" * 40)
        print(f"{Fore.CYAN}Total Accounts:{Fore.GREEN:>23} {total_accounts}")
        print(f"{Fore.CYAN}Active Accounts:{Fore.GREEN:>22} {active_accounts}")
        print(f"{Fore.CYAN}Inactive Accounts:{Fore.RED:>20} {inactive_accounts}")
        
        if total_accounts > 0:
            active_percent = (active_accounts / total_accounts) * 100
            print(f"{Fore.CYAN}Active Rate:{Fore.GREEN:>27} {active_percent:.1f}%")
        
        print()
        
        # Account Actions
        print(Fore.YELLOW + "ACTIONS")
        print(Fore.CYAN + "-" * 40)
        
        actions = [
            ("1", "Add Account", "Add new account"),
            ("2", "Import Accounts", "Import from file"),
            ("3", "Export Accounts", "Save to file"),
            ("4", "Check Accounts", "Validate all"),
            ("5", "View Accounts", "Show list"),
            ("6", "Create Dummy", "Create test accounts"),
            ("7", "Back to Main", "Return")
        ]
        
        for action_id, action_name, description in actions:
            print(f"{Fore.GREEN}[{action_id}] {Fore.WHITE}{action_name:20} {Fore.CYAN}- {description}")
        
        print()
        choice = input(Fore.YELLOW + "Select action [1-7]: " + Fore.WHITE)
        return choice
    
    def show_settings(self, settings_data: Dict):
        """Show settings interface"""
        self.clear_screen()
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "⚙️ SETTINGS")
        print(Fore.CYAN + "=" * 70)
        print()
        
        # Current Settings
        print(Fore.YELLOW + "CURRENT SETTINGS")
        print(Fore.CYAN + "-" * 40)
        
        for category, settings in settings_data.items():
            print(f"\n{Fore.MAGENTA}{category.upper()}")
            for key, value in settings.items():
                print(f"  {Fore.CYAN}{key:25} {Fore.WHITE}{value}")
        
        print()
        
        # Settings Actions
        print(Fore.YELLOW + "ACTIONS")
        print(Fore.CYAN + "-" * 40)
        
        actions = [
            ("1", "Edit Settings", "Modify configuration"),
            ("2", "Reset to Default", "Restore defaults"),
            ("3", "Save Settings", "Save to file"),
            ("4", "Load Settings", "Load from file"),
            ("5", "Back to Main", "Return")
        ]
        
        for action_id, action_name, description in actions:
            print(f"{Fore.GREEN}[{action_id}] {Fore.WHITE}{action_name:20} {Fore.CYAN}- {description}")
        
        print()
        choice = input(Fore.YELLOW + "Select action [1-5]: " + Fore.WHITE)
        return choice
    
    def show_help(self):
        """Show help information"""
        self.clear_screen()
        
        print(Fore.CYAN + "=" * 70)
        print(Fore.GREEN + "❓ HELP & DOCUMENTATION")
        print(Fore.CYAN + "=" * 70)
        print()
        
        sections = [
            ("Getting Started", [
                "1. Install Python 3.8+",
                "2. Run 'pip install -r requirements.txt'",
                "3. Run 'python main.py'",
                "4. Add proxies to proxies.txt",
                "5. Configure settings in settings.json"
            ]),
            
            ("How to Use", [
                "1. Start the bot from main menu",
                "2. Add view tasks using 'Send Views'",
                "3. Monitor progress in dashboard",
                "4. Check statistics regularly",
                "5. Stop bot when done"
            ]),
            
            ("Methods Explained", [
                "Browser: Most reliable, uses real browser",
                "API: Fast but may be detected",
                "Multi-Account: Uses multiple accounts",
                "Auto: Bot chooses best method"
            ]),
            
            ("Troubleshooting", [
                "Views not counting? Try Browser method",
                "Proxies failing? Check proxy.txt file",
                "Slow performance? Reduce concurrent tasks",
                "Errors? Check logs/bot.log"
            ]),
            
            ("Safety Tips", [
                "Use dummy accounts only",
                "Rotate proxies frequently",
                "Limit views per video",
                "Add delays between views",
                "Monitor for bans"
            ])
        ]
        
        for section_title, items in sections:
            print(Fore.YELLOW + f"\n{section_title}")
            print(Fore.CYAN + "-" * 40)
            for item in items:
                print(Fore.WHITE + f"  • {item}")
        
        print(Fore.CYAN + "\n" + "=" * 70)
        input(Fore.YELLOW + "\nPress Enter to continue..." + Fore.WHITE)
    
    def show_message(self, message: str, msg_type: str = "info", duration: int = 3):
        """Show message with color coding"""
        colors = {
            'info': Fore.CYAN,
            'success': Fore.GREEN,
            'warning': Fore.YELLOW,
            'error': Fore.RED
        }
        
        color = colors.get(msg_type, Fore.WHITE)
        print(f"\n{color}{message}{Fore.RESET}")
        
        if duration > 0:
            time.sleep(duration)
    
    def show_error(self, error_msg: str, details: str = ""):
        """Show error message"""
        print(Fore.RED + "\n" + "!" * 70)
        print(Fore.RED + "ERROR")
        print(Fore.RED + "!" * 70)
        print(Fore.WHITE + f"\n{error_msg}")
        
        if details:
            print(Fore.YELLOW + f"\nDetails: {details}")
        
        print(Fore.RED + "\n" + "!" * 70)
        input(Fore.YELLOW + "\nPress Enter to continue..." + Fore.WHITE)
    
    def show_success(self, message: str):
        """Show success message"""
        print(Fore.GREEN + "\n" + "✓" * 70)
        print(Fore.GREEN + "SUCCESS")
        print(Fore.GREEN + "✓" * 70)
        print(Fore.WHITE + f"\n{message}")
        print(Fore.GREEN + "✓" * 70)
        time.sleep(2)
    
    def show_loading(self, message: str, duration: float = 0.5):
        """Show loading animation"""
        spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        
        end_time = time.time() + duration
        i = 0
        
        while time.time() < end_time:
            sys.stdout.write(f"\r{Fore.CYAN}{spinner[i % len(spinner)]} {Fore.WHITE}{message}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        
        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
        sys.stdout.flush()
    
    def check_keypress(self) -> bool:
        """Check for key press (non-blocking)"""
        try:
            import msvcrt  # Windows
            return msvcrt.kbhit()
        except ImportError:
            try:
                import sys
                import select
                return select.select([sys.stdin], [], [], 0)[0] != []
            except:
                return False
    
    def get_keypress(self) -> str:
        """Get key press"""
        try:
            import msvcrt  # Windows
            return msvcrt.getch().decode()
        except ImportError:
            try:
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                return ch
            except:
                return ''