"""
Advanced Text Formatter
Professional text formatting utilities
"""

import textwrap
from typing import List, Dict, Any, Tuple
from datetime import datetime

from config import Colors

def create_table(
    data: List[List[Any]], 
    headers: List[str] = None,
    max_width: int = 80
) -> str:
    """
    Create a formatted ASCII table
    
    Args:
        data: Table data (list of rows)
        headers: Column headers
        max_width: Maximum table width
    
    Returns:
        Formatted table string
    """
    if not data:
        return "No data"
    
    # Calculate column widths
    if headers:
        all_rows = [headers] + data
    else:
        all_rows = data
    
    col_count = len(all_rows[0])
    col_widths = [0] * col_count
    
    for row in all_rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)
            col_widths[i] = max(col_widths[i], len(cell_str))
    
    # Adjust for max width
    total_width = sum(col_widths) + (3 * (col_count - 1)) + 4
    if total_width > max_width:
        # Reduce column widths proportionally
        excess = total_width - max_width
        for i in range(col_count):
            reduction = int((col_widths[i] / total_width) * excess)
            col_widths[i] = max(col_widths[i] - reduction, 10)
    
    # Create table
    lines = []
    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    # Add headers
    if headers:
        lines.append(border)
        header_row = "|"
        for i, header in enumerate(headers):
            header_row += f" {header:<{col_widths[i]}} |"
        lines.append(header_row)
        lines.append(border)
    
    # Add data rows
    for row in data:
        row_str = "|"
        for i, cell in enumerate(row):
            cell_str = str(cell)
            # Truncate if too long
            if len(cell_str) > col_widths[i]:
                cell_str = cell_str[:col_widths[i]-3] + "..."
            row_str += f" {cell_str:<{col_widths[i]}} |"
        lines.append(row_str)
    
    lines.append(border)
    
    return "\n".join(lines)

def create_progress_bar(
    percentage: float, 
    width: int = 50,
    filled_char: str = "█",
    empty_char: str = "░"
) -> str:
    """
    Create a visual progress bar
    
    Args:
        percentage: Progress percentage (0-100)
        width: Bar width in characters
        filled_char: Character for filled portion
        empty_char: Character for empty portion
    
    Returns:
        Progress bar string
    """
    percentage = max(0, min(100, percentage))
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width
    
    # Color based on percentage
    if percentage < 30:
        color = Colors.RED
    elif percentage < 70:
        color = Colors.YELLOW
    else:
        color = Colors.GREEN
    
    bar = f"{color}{filled_char * filled_width}{Colors.RESET}{empty_char * empty_width}"
    return f"[{bar}] {percentage:.1f}%"

def format_number(num: int) -> str:
    """
    Format large numbers with commas
    
    Args:
        num: Number to format
    
    Returns:
        Formatted string
    """
    return f"{num:,}"

def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human readable format
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string (e.g., "2h 30m")
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {minutes}m"
    
    days, hours = divmod(hours, 24)
    return f"{days}d {hours}h"

def center_text(text: str, width: int = 80) -> str:
    """
    Center text within given width
    
    Args:
        text: Text to center
        width: Total width
    
    Returns:
        Centered text
    """
    return text.center(width)

def box_text(
    text: str, 
    width: int = 60,
    padding: int = 1,
    border_char: str = "═",
    corner_char: str = "╔╗╚╝"
) -> str:
    """
    Create a box around text
    
    Args:
        text: Text to box
        width: Box width
        padding: Padding inside box
        border_char: Border character
        corner_char: Corner characters (top-left, top-right, bottom-left, bottom-right)
    
    Returns:
        Boxed text
    """
    if len(corner_char) != 4:
        corner_char = "┌┐└┘"
    
    tl, tr, bl, br = corner_char
    
    lines = textwrap.wrap(text, width - (padding * 2) - 2)
    
    # Top border
    result = tl + border_char * (width - 2) + tr + "\n"
    
    # Padding top
    for _ in range(padding):
        result += "│" + " " * (width - 2) + "│\n"
    
    # Text lines
    for line in lines:
        padded_line = line.center(width - 2)
        result += f"│{padded_line}│\n"
    
    # Padding bottom
    for _ in range(padding):
        result += "│" + " " * (width - 2) + "│\n"
    
    # Bottom border
    result += bl + border_char * (width - 2) + br
    
    return result

def colorize_by_percentage(value: float, reverse: bool = False) -> str:
    """
    Colorize text based on percentage value
    
    Args:
        value: Percentage value (0-100)
        reverse: Reverse color scale (green for low, red for high)
    
    Returns:
        Color code string
    """
    if reverse:
        if value < 30:
            return Colors.GREEN
        elif value < 70:
            return Colors.YELLOW
        else:
            return Colors.RED
    else:
        if value < 30:
            return Colors.RED
        elif value < 70:
            return Colors.YELLOW
        else:
            return Colors.GREEN

def format_timestamp(timestamp: datetime = None) -> str:
    """
    Format timestamp for display
    
    Args:
        timestamp: Datetime object (default: current time)
    
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def format_list(items: List[str], bullet: str = "•") -> str:
    """
    Format list with bullets
    
    Args:
        items: List of items
        bullet: Bullet character
    
    Returns:
        Formatted list string
    """
    return "\n".join([f"{bullet} {item}" for item in items])

def format_key_value(
    data: Dict[str, Any], 
    key_width: int = 20,
    separator: str = ": "
) -> str:
    """
    Format key-value pairs
    
    Args:
        data: Dictionary of key-value pairs
        key_width: Width for keys
        separator: Separator between key and value
    
    Returns:
        Formatted string
    """
    lines = []
    for key, value in data.items():
        key_str = f"{key:{key_width}}"
        lines.append(f"{Colors.CYAN}{key_str}{Colors.RESET}{separator}{value}")
    
    return "\n".join(lines)

def truncate_text(text: str, max_length: int, ellipsis: str = "...") -> str:
    """
    Truncate text with ellipsis
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: Ellipsis string
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(ellipsis)] + ellipsis

def create_header(text: str, width: int = 60, char: str = "=") -> str:
    """
    Create a header with centered text
    
    Args:
        text: Header text
        width: Total width
        char: Border character
    
    Returns:
        Header string
    """
    border = char * width
    centered = text.center(width)
    
    return f"\n{border}\n{centered}\n{border}\n"

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage with color
    
    Args:
        value: Percentage value
        decimals: Decimal places
    
    Returns:
        Formatted percentage string with color
    """
    color = colorize_by_percentage(value)
    return f"{color}{value:.{decimals}f}%{Colors.RESET}"