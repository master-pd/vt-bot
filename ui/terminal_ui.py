"""
Terminal User Interface
Professional Interactive Terminal
"""

import asyncio
import sys
import os
from typing import Optional, Dict
from dataclasses import dataclass

from utils.logger import setup_logger
from ui.banner import display_banner, print_colored
from ui.formatter import (
    create_table, create_progress_bar, 
    format_number, center_text, box_text
)
from config import Colors, UI_REFRESH_INTERVAL

logger = setup_logger(__name__)

@dataclass
class MenuItem:
    """Menu item data class"""
    id: str
    title: str
    handler: callable
    description: str = ""
    shortcut: str = ""

class TerminalUI:
    """Interactive Terminal UI"""
    
    def __init__(self, engine):
        self.engine = engine
        self.running = False
        self.current_menu = "main"
        self.menus = self._create_menus()
        
    def _create_menus(self):
        """Create all menus"""
        return {
            "main": [
                MenuItem("1", "🚀 Start View Test", self.start_test, "Send views to TikTok video"),
                MenuItem("2", "📊 View Statistics", self.show_stats, "Show system statistics"),
                MenuItem("3", "👤 Account Manager", self.account_manager, "Manage TikTok accounts"),
                MenuItem("4", "🔗 Proxy Manager", self.proxy_manager, "Manage proxies"),
                MenuItem("5", "⚙️ Settings", self.settings_menu, "System settings"),
                MenuItem("6", "🤖 Start Bot", self.start_bot, "Start Telegram bot"),
                MenuItem("0", "❌ Exit", self.exit_app, "Exit application")
            ],
            "account": [
                MenuItem("1", "➕ Add Accounts", self.add_accounts, "Add TikTok accounts"),
                MenuItem("2", "📋 List Accounts", self.list_accounts, "Show all accounts"),
                MenuItem("3", "🧹 Clean Banned", self.clean_banned, "Remove banned accounts"),
                MenuItem("4", "📊 Account Stats", self.account_stats, "Account statistics"),
                MenuItem("0", "🔙 Back", self.back_to_main, "Return to main menu")
            ],
            "proxy": [
                MenuItem("1", "➕ Add Proxies", self.add_proxies, "Add proxy servers"),
                MenuItem("2", "📋 List Proxies", self.list_proxies, "Show all proxies"),
                MenuItem("3", "🧪 Test Proxies", self.test_proxies, "Test proxy connectivity"),
                MenuItem("4", "📊 Proxy Stats", self.proxy_stats, "Proxy statistics"),
                MenuItem("0", "🔙 Back", self.back_to_main, "Return to main menu")
            ]
        }
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_menu(self, menu_name: str):
        """Display a menu"""
        menu_items = self.menus.get(menu_name, [])
        
        print_colored(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print_colored(f"{Colors.YELLOW}{Colors.BOLD}📋 {menu_name.upper()} MENU{Colors.RESET}")
        print_colored(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        for item in menu_items:
            shortcut_display = f" [{item.shortcut}]" if item.shortcut else ""
            print_colored(
                f"{Colors.GREEN}[{item.id}]{Colors.RESET} {item.title}{shortcut_display}"
            )
            if item.description:
                print_colored(f"     {Colors.WHITE}› {item.description}{Colors.RESET}")
            print()
    
    async def get_input(self, prompt: str = "> ") -> str:
        """Get user input"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, input, f"{Colors.BLUE}{prompt}{Colors.RESET}"
            )
        except (KeyboardInterrupt, EOFError):
            return "0"
    
    async def start_test(self):
        """Start a view test"""
        self.clear_screen()
        display_banner("START VIEW TEST")
        
        print_colored(f"{Colors.YELLOW}🎬 Enter TikTok Video URL{Colors.RESET}")
        print_colored(f"{Colors.WHITE}Example: https://www.tiktok.com/@user/video/123456789{Colors.RESET}\n")
        
        video_url = await self.get_input("Video URL: ")
        
        if not video_url:
            print_colored(f"{Colors.RED}❌ URL cannot be empty!{Colors.RESET}")
            return
        
        print_colored(f"\n{Colors.YELLOW}🔢 Enter Number of Views{Colors.RESET}")
        print_colored(f"{Colors.WHITE}Max: 10,000 views per minute{Colors.RESET}\n")
        
        try:
            view_count = int(await self.get_input("Views count: "))
            
            if view_count <= 0:
                print_colored(f"{Colors.RED}❌ View count must be positive!{Colors.RESET}")
                return
                
            if view_count > 10000:
                print_colored(f"{Colors.YELLOW}⚠️  High view count. This may take time.{Colors.RESET}")
                
        except ValueError:
            print_colored(f"{Colors.RED}❌ Invalid number!{Colors.RESET}")
            return
        
        # Confirm
        print_colored(f"\n{Colors.YELLOW}📋 Confirm Test{Colors.RESET}")
        print_colored(f"{Colors.WHITE}URL: {video_url}{Colors.RESET}")
        print_colored(f"{Colors.WHITE}Views: {view_count}{Colors.RESET}")
        
        confirm = await self.get_input("\nStart test? (y/n): ")
        
        if confirm.lower() == 'y':
            print_colored(f"{Colors.GREEN}🚀 Starting view test...{Colors.RESET}")
            
            try:
                task_id = await self.engine.create_task(video_url, view_count)
                print_colored(f"{Colors.GREEN}✅ Task created: {task_id}{Colors.RESET}")
                
                # Show progress
                await self.show_task_progress(task_id)
                
            except Exception as e:
                print_colored(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
        else:
            print_colored(f"{Colors.YELLOW}⏹️  Test cancelled{Colors.RESET}")
    
    async def show_task_progress(self, task_id: str):
        """Show task progress"""
        print_colored(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print_colored(f"{Colors.YELLOW}📊 Task Progress: {task_id}{Colors.RESET}")
        print_colored(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        while True:
            task_info = self.engine.get_task_status(task_id)
            
            if not task_info:
                print_colored(f"{Colors.RED}❌ Task not found{Colors.RESET}")
                break
            
            if task_info["status"] in ["completed", "cancelled"]:
                break
            
            # Calculate progress
            total = task_info["view_count"]
            sent = task_info["views_sent"]
            progress = (sent / total) * 100 if total > 0 else 0
            
            # Display progress
            progress_bar = create_progress_bar(progress, width=50)
            
            print_colored(f"\r{Colors.BLUE}Progress: {progress_bar} {progress:.1f}%", end="")
            print_colored(f" | Sent: {sent}/{total} | Failed: {task_info['views_failed']}", end="")
            
            await asyncio.sleep(UI_REFRESH_INTERVAL)
        
        print_colored(f"\n\n{Colors.GREEN}✅ Task completed!{Colors.RESET}")
        await asyncio.sleep(2)
    
    async def show_stats(self):
        """Show system statistics"""
        self.clear_screen()
        display_banner("SYSTEM STATISTICS")
        
        stats = self.engine.get_stats()
        
        # Create stats table
        table_data = [
            ["Total Views Sent", format_number(stats["total_views_sent"])],
            ["Total Views Failed", format_number(stats["total_views_failed"])],
            ["Active Tasks", str(stats["active_tasks"])],
            ["Available Proxies", str(stats["available_proxies"])],
            ["Available Accounts", str(stats["available_accounts"])],
            ["Requests/Minute", f"{stats['requests_per_minute']:.1f}"],
            ["System Status", "🟢 Running" if stats["running"] else "🔴 Stopped"]
        ]
        
        table = create_table(table_data, headers=["Metric", "Value"])
        print_colored(table)
        
        await self.get_input("\nPress Enter to continue...")
    
    async def account_manager(self):
        """Account manager menu"""
        self.current_menu = "account"
        await self.run_menu("account")
    
    async def proxy_manager(self):
        """Proxy manager menu"""
        self.current_menu = "proxy"
        await self.run_menu("proxy")
    
    async def settings_menu(self):
        """Settings menu"""
        self.clear_screen()
        display_banner("SETTINGS")
        
        print_colored(f"{Colors.YELLOW}⚙️  System Settings{Colors.RESET}\n")
        
        # Settings options would go here
        print_colored(f"{Colors.GREEN}[1]{Colors.RESET} View Settings")
        print_colored(f"{Colors.GREEN}[2]{Colors.RESET} Engine Settings")
        print_colored(f"{Colors.GREEN}[3]{Colors.RESET} Proxy Settings")
        print_colored(f"{Colors.GREEN}[4]{Colors.RESET} Account Settings")
        print_colored(f"{Colors.GREEN}[0]{Colors.RESET} Back\n")
        
        choice = await self.get_input("Select option: ")
        
        # Handle settings choices
        if choice == "0":
            self.current_menu = "main"
    
    async def start_bot(self):
        """Start Telegram bot"""
        self.clear_screen()
        display_banner("TELEGRAM BOT")
        
        print_colored(f"{Colors.YELLOW}🤖 Starting Telegram Bot...{Colors.RESET}\n")
        
        try:
            from bot.telegram_bot import start_bot
            print_colored(f"{Colors.GREEN}✅ Bot is starting...{Colors.RESET}")
            print_colored(f"{Colors.YELLOW}⚠️  Press Ctrl+C to stop the bot{Colors.RESET}")
            
            # Run bot in background
            asyncio.create_task(start_bot())
            
            await self.get_input("\nBot started. Press Enter to return...")
            
        except ImportError:
            print_colored(f"{Colors.RED}❌ Telegram bot module not available{Colors.RESET}")
            await asyncio.sleep(2)
        except Exception as e:
            print_colored(f"{Colors.RED}❌ Error starting bot: {e}{Colors.RESET}")
            await asyncio.sleep(2)
    
    async def exit_app(self):
        """Exit application"""
        print_colored(f"\n{Colors.YELLOW}👋 Exiting VT View Tester...{Colors.RESET}")
        self.running = False
        await self.engine.shutdown()
        sys.exit(0)
    
    async def back_to_main(self):
        """Return to main menu"""
        self.current_menu = "main"
    
    async def run_menu(self, menu_name: str):
        """Run a specific menu"""
        while self.running and self.current_menu == menu_name:
            self.clear_screen()
            display_banner(menu_name.upper())
            self.display_menu(menu_name)
            
            choice = await self.get_input("Select option: ")
            
            if choice == "0":
                self.current_menu = "main"
                break
            
            # Find and execute menu item
            menu_items = self.menus.get(menu_name, [])
            selected_item = next((item for item in menu_items if item.id == choice), None)
            
            if selected_item:
                try:
                    if asyncio.iscoroutinefunction(selected_item.handler):
                        await selected_item.handler()
                    else:
                        selected_item.handler()
                except Exception as e:
                    print_colored(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")
                    await asyncio.sleep(2)
            else:
                print_colored(f"{Colors.RED}❌ Invalid option!{Colors.RESET}")
                await asyncio.sleep(1)
    
    async def run(self):
        """Main UI run loop"""
        self.running = True
        self.clear_screen()
        
        # Display welcome banner
        display_banner("WELCOME")
        
        print_colored(f"{Colors.GREEN}🚀 VT View Tester is ready!{Colors.RESET}\n")
        
        while self.running:
            await self.run_menu(self.current_menu)