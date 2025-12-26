"""
Stylish Banners and UI Elements
Professional terminal UI components
"""

import os
import sys
import time
from typing import List, Optional
from datetime import datetime

from config import Colors, PROJECT_NAME, VERSION, AUTHOR

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text: str, color: str = Colors.RESET, end: str = "\n"):
    """Print colored text"""
    print(f"{color}{text}{Colors.RESET}", end=end)

def display_banner(title: str = ""):
    """Display main banner with title"""
    clear_screen()
    
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    ██╗   ██╗████████╗     ██╗   ██╗██╗███████╗██╗    ██╗             ║
║    ██║   ██║╚══██╔══╝     ██║   ██║██║██╔════╝██║    ██║             ║
║    ██║   ██║   ██║        ██║   ██║██║█████╗  ██║ █╗ ██║             ║
║    ╚██╗ ██╔╝   ██║        ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║             ║
║     ╚████╔╝    ██║         ╚████╔╝ ██║███████╗╚███╔███╔╝             ║
║      ╚═══╝     ╚═╝          ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝              ║
║                                                                      ║
║               {Colors.YELLOW}{Colors.BOLD}{PROJECT_NAME} v{VERSION}{Colors.CYAN}{Colors.BOLD}                 ║
║               {Colors.MAGENTA}Developed by: {AUTHOR}{Colors.CYAN}{Colors.BOLD}                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
    
    print(banner)
    
    if title:
        title_banner = f"""
{Colors.YELLOW}{Colors.BOLD}{'═' * 60}{Colors.RESET}
{Colors.GREEN}{Colors.BOLD}{title.center(60)}{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}{'═' * 60}{Colors.RESET}
"""
        print(title_banner)

def display_status_bar(status: str, progress: float = 0):
    """Display status bar with progress"""
    width = 50
    filled = int(width * progress)
    empty = width - filled
    
    bar = f"{Colors.GREEN}█" * filled + f"{Colors.WHITE}░" * empty + Colors.RESET
    percentage = f"{progress * 100:.1f}%"
    
    status_bar = f"""
{Colors.CYAN}{'─' * 60}{Colors.RESET}
{Colors.BOLD}Status:{Colors.RESET} {status}
{Colors.BOLD}Progress:{Colors.RESET} [{bar}] {percentage}
{Colors.CYAN}{'─' * 60}{Colors.RESET}
"""
    print(status_bar)

def display_menu(options: List[str], title: str = "Menu"):
    """Display interactive menu"""
    print_colored(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print_colored(f"{Colors.YELLOW}{Colors.BOLD}{title.center(60)}{Colors.RESET}")
    print_colored(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")
    
    for i, option in enumerate(options, 1):
        print_colored(f"{Colors.GREEN}[{i}]{Colors.RESET} {option}")
    
    print_colored(f"\n{Colors.CYAN}{'─' * 60}{Colors.RESET}")
    return len(options)

def display_stats(stats: dict):
    """Display statistics in a formatted way"""
    print_colored(f"\n{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print_colored(f"{Colors.YELLOW}{Colors.BOLD}{'SYSTEM STATISTICS'.center(60)}{Colors.RESET}")
    print_colored(f"{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")
    
    for key, value in stats.items():
        key_formatted = key.replace('_', ' ').title()
        
        if isinstance(value, (int, float)) and key.endswith('rate'):
            # Color code success rates
            if value < 30:
                color = Colors.RED
            elif value < 70:
                color = Colors.YELLOW
            else:
                color = Colors.GREEN
            value_str = f"{color}{value:.1f}%{Colors.RESET}"
        elif isinstance(value, (int, float)) and key.endswith('count'):
            value_str = f"{Colors.CYAN}{value:,}{Colors.RESET}"
        else:
            value_str = str(value)
        
        print_colored(f"{Colors.BOLD}{key_formatted}:{Colors.RESET} {value_str}")
    
    print_colored(f"\n{Colors.CYAN}{'─' * 60}{Colors.RESET}")

def display_table(headers: List[str], rows: List[List[str]], title: str = ""):
    """Display data in a table format"""
    if title:
        print_colored(f"\n{Colors.YELLOW}{Colors.BOLD}{title}{Colors.RESET}")
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print header
    header_row = "│"
    for i, header in enumerate(headers):
        header_row += f" {header:<{col_widths[i]}} │"
    
    border = "┌" + "┬".join(["─" * (w + 2) for w in col_widths]) + "┐"
    separator = "├" + "┼".join(["─" * (w + 2) for w in col_widths]) + "┤"
    bottom = "└" + "┴".join(["─" * (w + 2) for w in col_widths]) + "┘"
    
    print_colored(border)
    print_colored(header_row)
    print_colored(separator)
    
    # Print rows
    for row in rows:
        row_str = "│"
        for i, cell in enumerate(row):
            row_str += f" {str(cell):<{col_widths[i]}} │"
        print_colored(row_str)
    
    print_colored(bottom)

def display_progress_animation(text: str = "Processing", duration: int = 3):
    """Display progress animation"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    print_colored(f"\n{Colors.BLUE}{text}...{Colors.RESET}", end=" ")
    
    start_time = time.time()
    frame_idx = 0
    
    try:
        while time.time() - start_time < duration:
            print_colored(f"\r{Colors.BLUE}{text}... {frames[frame_idx % len(frames)]}{Colors.RESET}", end="")
            sys.stdout.flush()
            time.sleep(0.1)
            frame_idx += 1
        
        print_colored(f"\r{Colors.GREEN}{text}... ✓ Done!{Colors.RESET}")
        
    except KeyboardInterrupt:
        print_colored(f"\r{Colors.YELLOW}{text}... ⚠️  Cancelled{Colors.RESET}")

def display_warning(message: str):
    """Display warning message"""
    print_colored(f"\n{Colors.YELLOW}{'⚠️ ' * 3} WARNING {'⚠️ ' * 3}{Colors.RESET}")
    print_colored(f"{Colors.YELLOW}{message}{Colors.RESET}")
    print_colored(f"{Colors.YELLOW}{'⚠️ ' * 3}{' ' * 8}{'⚠️ ' * 3}{Colors.RESET}\n")

def display_success(message: str):
    """Display success message"""
    print_colored(f"\n{Colors.GREEN}{'✅ ' * 3} SUCCESS {'✅ ' * 3}{Colors.RESET}")
    print_colored(f"{Colors.GREEN}{message}{Colors.RESET}")
    print_colored(f"{Colors.GREEN}{'✅ ' * 3}{' ' * 8}{'✅ ' * 3}{Colors.RESET}\n")

def display_error(message: str):
    """Display error message"""
    print_colored(f"\n{Colors.RED}{'❌ ' * 3} ERROR {'❌ ' * 3}{Colors.RESET}")
    print_colored(f"{Colors.RED}{message}{Colors.RESET}")
    print_colored(f"{Colors.RED}{'❌ ' * 3}{' ' * 8}{'❌ ' * 3}{Colors.RESET}\n")

def display_info(message: str):
    """Display info message"""
    print_colored(f"\n{Colors.CYAN}{'ℹ️ ' * 3} INFO {'ℹ️ ' * 3}{Colors.RESET}")
    print_colored(f"{Colors.CYAN}{message}{Colors.RESET}")
    print_colored(f"{Colors.CYAN}{'ℹ️ ' * 3}{' ' * 8}{'ℹ️ ' * 3}{Colors.RESET}\n")

def display_countdown(seconds: int, message: str = "Starting in"):
    """Display countdown"""
    print_colored(f"\n{Colors.YELLOW}{message}...{Colors.RESET}")
    
    for i in range(seconds, 0, -1):
        print_colored(f"\r{Colors.CYAN}{i}...{Colors.RESET}", end="")
        sys.stdout.flush()
        time.sleep(1)
    
    print_colored(f"\r{Colors.GREEN}Starting now!{Colors.RESET}\n")

def display_logo():
    """Display ASCII art logo"""
    logo = f"""
{Colors.MAGENTA}
  ██████╗ ███████╗██╗   ██╗███████╗██╗  ██╗███████╗██████╗ 
  ██╔══██╗██╔════╝██║   ██║██╔════╝██║  ██║██╔════╝██╔══██╗
  ██║  ██║█████╗  ██║   ██║███████╗███████║█████╗  ██████╔╝
  ██║  ██║██╔══╝  ╚██╗ ██╔╝╚════██║██╔══██║██╔══╝  ██╔══██╗
  ██████╔╝███████╗ ╚████╔╝ ███████║██║  ██║███████╗██║  ██║
  ╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
{Colors.RESET}
    """
    print(logo)

def display_footer():
    """Display footer with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    footer = f"""
{Colors.CYAN}{'─' * 60}{Colors.RESET}
{Colors.WHITE}© {datetime.now().year} {PROJECT_NAME} | Version: {VERSION} | Time: {timestamp}{Colors.RESET}
{Colors.CYAN}{'─' * 60}{Colors.RESET}
    """
    print(footer)

def get_user_input(prompt: str, color: str = Colors.BLUE) -> str:
    """Get user input with colored prompt"""
    try:
        return input(f"{color}{prompt}{Colors.RESET}")
    except (KeyboardInterrupt, EOFError):
        return ""

def confirm_action(message: str) -> bool:
    """Confirm action with user"""
    response = get_user_input(f"{message} (y/n): ", Colors.YELLOW)
    return response.lower() in ['y', 'yes', '1']