"""Render - Full rendering engine with animations"""

import os
import sys
import time
import subprocess
from typing import Optional, List, Tuple
from enum import Enum


class AnsiCode:
    """ANSI escape codes"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    
    FG_BLACK = "\033[30m"
    FG_RED = "\033[31m"
    FG_GREEN = "\033[32m"
    FG_YELLOW = "\033[33m"
    FG_BLUE = "\033[34m"
    FG_MAGENTA = "\033[35m"
    FG_CYAN = "\033[36m"
    FG_WHITE = "\033[37m"
    FG_DEFAULT = "\033[39m"
    FG_LIGHT_BLACK = "\033[90m"
    FG_LIGHT_RED = "\033[91m"
    FG_LIGHT_GREEN = "\033[92m"
    FG_LIGHT_YELLOW = "\033[93m"
    FG_LIGHT_BLUE = "\033[94m"
    FG_LIGHT_MAGENTA = "\033[95m"
    FG_LIGHT_CYAN = "\033[96m"
    FG_LIGHT_WHITE = "\033[97m"
    
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size"""
    try:
        if os.name == 'nt':
            from ctypes import windll, create_string_buffer
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                import struct
                bufx, bufy, curx, cury, wattr = struct.unpack("hhhhH", csbi.raw)
                width = curx - csbi[0] + 1
                height = cury - csbi[1] + 1
                return width, height
        else:
            import fcntl
            import termios
            import struct
            try:
                with open(os.ctermid(), "rb") as f:
                    cr = struct.unpack("hh", fcntl.ioctl(f.fileno(), termios.TIOCGWINSZ, "1234"))
                    return cr[1], cr[0]
            except:
                pass
    except:
        pass
    return 80, 24


def clear_screen():
    """Clear the screen"""
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def move_cursor(x: int, y: int):
    """Move cursor to position"""
    sys.stdout.write(f"\033[{y};{x}H")
    sys.stdout.flush()


def hide_cursor():
    """Hide cursor"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    """Show cursor"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def save_cursor():
    """Save cursor position"""
    sys.stdout.write("\033[s")
    sys.stdout.flush()


def restore_cursor():
    """Restore cursor position"""
    sys.stdout.write("\u001b[u")
    sys.stdout.flush()


def erase_line():
    """Erase current line"""
    sys.stdout.write("\033[2K")
    sys.stdout.flush()


def erase_display():
    """Erase display"""
    sys.stdout.write("\033[3J")
    sys.stdout.flush()


def write(text: str = ""):
    """Write text"""
    sys.stdout.write(text)
    sys.stdout.flush()


def write_line(text: str = ""):
    """Write line"""
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except:
        pass


def move_cursor(x: int, y: int):
    """Move cursor to position"""
    sys.stdout.write(f"\033[{y};{x}H")
    sys.stdout.flush()


def hide_cursor():
    """Hide cursor"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    """Show cursor"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def save_cursor():
    """Save cursor position"""
    sys.stdout.write("\033[s")
    sys.stdout.flush()


def restore_cursor():
    """Restore cursor position"""
    sys.stdout.write("\u001b[u")
    sys.stdout.flush()


def erase_line():
    """Erase current line"""
    sys.stdout.write("\033[2K")
    sys.stdout.flush()


def erase_display():
    """Erase display"""
    sys.stdout.write("\033[3J")
    sys.stdout.flush()


def style(text: str, bold: bool = False, italic: bool = False, 
          underline: bool = False, color: Optional[str] = None,
          bg_color: Optional[str] = None, dim: bool = False,
          blink: bool = False, reverse: bool = False) -> str:
    """Style text with ANSI codes"""
    codes = []
    
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if italic:
        codes.append("3")
    if underline:
        codes.append("4")
    if blink:
        codes.append("5")
    if reverse:
        codes.append("7")
    
    color_codes = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "reset": "0", "gray": "90", "grey": "90",
        "bright_red": "91", "bright_green": "92", "bright_yellow": "93",
        "bright_blue": "94", "bright_magenta": "95", "bright_cyan": "96",
        "bright_white": "97",
    }
    bg_color_codes = {
        "black": "40", "red": "41", "green": "42", "yellow": "43",
        "blue": "44", "magenta": "45", "cyan": "46", "white": "47",
    }
    
    if color:
        codes.append(color_codes.get(color, "37"))
    if bg_color:
        codes.append(bg_color_codes.get(bg_color, "49"))
    
    if codes:
        return f"\033[{';'.join(codes)}m{text}\033[0m"
    return text


def write(text: str = ""):
    """Write text"""
    sys.stdout.write(text)
    sys.stdout.flush()


def write_line(text: str = ""):
    """Write line"""
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def word_wrap(text: str, width: int) -> List[str]:
    """Word wrap text"""
    words = text.split()
    lines = []
    current = ""
    
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = current + " " + word if current else word
        else:
            if current:
                lines.append(current)
            current = word
    
    if current:
        lines.append(current)
    
    return lines


class BorderStyle(Enum):
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    ROUNDED = "rounded"
    ASCII = "ascii"


DOUBLE_BORDER = BorderStyle.DOUBLE
SINGLE_BORDER = BorderStyle.SINGLE
ROUNDED_BORDER = BorderStyle.ROUNDED
ASCII_BORDER = BorderStyle.ASCII


def draw_box(content: List[str], width: int, height: int, 
             border: BorderStyle = BorderStyle.SINGLE,
             title: str = "", color: str = "white") -> List[str]:
    """Draw a box with content"""
    
    if border == BorderStyle.DOUBLE:
        tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
    elif border == BorderStyle.ROUNDED:
        tl, tr, bl, br, h, v = "╭", "╮", "╰", "╯", "─", "│"
    elif border == BorderStyle.ASCII:
        tl, tr, bl, br, h, v = "+", "+", "+", "+", "-", "|"
    else:
        tl, tr, bl, br, h, v = "┌", "┐", "└", "┘", "─", "│"
    
    lines = []
    
    if title:
        title_line = f" {title} "
        title_len = len(title_line)
        top_len = width - 2
        if title_len < top_len:
            title_line = title_line.center(top_len, h)
        lines.append(tl + title_line + tr)
    else:
        lines.append(tl + h * (width - 2) + tr)
    
    for i in range(len(content), height - 2):
        content.append("")
    
    for line in content[:height - 2]:
        line = line[:width - 2]
        padding = " " * (width - len(line) - 2)
        lines.append(v + line + padding + v)
    
    lines.append(bl + h * (width - 2) + br)
    
    return lines


class ProgressBar:
    """Animated progress bar"""
    
    def __init__(self, width: int = 30):
        self.width = width
        self.progress = 0.0
        self.start_time = time.time()
    
    def update(self, progress: float):
        """Update progress"""
        self.progress = min(1.0, max(0.0, progress))
    
    def render(self, prefix: str = "") -> str:
        """Render progress bar"""
        filled = int(self.width * self.progress)
        bar = "█" * filled + "░" * (self.width - filled)
        percentage = int(self.progress * 100)
        
        elapsed = time.time() - self.start_time
        if self.progress > 0:
            eta = elapsed / self.progress * (1 - self.progress)
        else:
            eta = 0
        
        return f"{prefix}[{bar}] {percentage}% ETA: {eta:.1f}s"


class Spinner:
    """Animated spinner"""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, prefix: str = ""):
        self.frame = 0
        self.prefix = prefix
        self.running = False
    
    def next(self) -> str:
        """Get next frame"""
        frame = self.FRAMES[self.frame % len(self.FRAMES)]
        self.frame += 1
        return f"{self.prefix}{frame}"
    
    def render(self) -> str:
        """Render current frame"""
        return self.next()


class Animation:
    """Text animation effects"""
    
    @staticmethod
    def type_text(text: str, delay: float = 0.02) -> None:
        """Type text effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
    
    @staticmethod
    def fade_in(text: str, steps: int = 5) -> None:
        """Fade in effect"""
        for i in range(steps + 1):
            alpha = i / steps
            sys.stdout.write(f"\033[{38 + int(alpha * 23)}m{text}\033[0m\r")
            sys.stdout.flush()
            time.sleep(0.05)
        print()
    
    @staticmethod
    def slide_in(text: str, direction: str = "left") -> None:
        """Slide in effect"""
        width = get_terminal_size()[0]
        lines = text.split("\n")
        
        for line in lines:
            if direction == "right":
                line = line.rjust(width)
            print(line)
            time.sleep(0.02)
    
    @staticmethod
    def pulse(text: str, times: int = 3) -> None:
        """Pulse effect"""
        for _ in range(times):
            sys.stdout.write(f"\033[5m{text}\033[0m\r")
            sys.stdout.flush()
            time.sleep(0.3)
            sys.stdout.write(f"{' ' * len(text)}\r")
            sys.stdout.flush()
            time.sleep(0.1)


class Color:
    """Color palette"""
    
    PRIMARY = "#3b82f6"
    SECONDARY = "#8b5cf6"
    SUCCESS = "#22c55e"
    WARNING = "#eab308"
    ERROR = "#ef4444"
    INFO = "#06b6d4"
    
    DARK_BG = "#1e1e1e"
    DARK_SURFACE = "#252526"
    DARK_BORDER = "#3e3e42"
    
    LIGHT_BG = "#ffffff"
    LIGHT_SURFACE = "#f3f4f6"
    LIGHT_BORDER = "#d1d5db"
    
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#9ca3af"
    TEXT_MUTED = "#6b7280"


class Theme:
    """UI Theme"""
    
    def __init__(self, dark: bool = True):
        self.dark = dark
        
        if dark:
            self.bg = Color.DARK_BG
            self.surface = Color.DARK_SURFACE
            self.border = Color.DARK_BORDER
            self.text = Color.TEXT_PRIMARY
            self.text_secondary = Color.TEXT_SECONDARY
            self.text_muted = Color.TEXT_MUTED
        else:
            self.bg = Color.LIGHT_BG
            self.surface = Color.LIGHT_SURFACE
            self.border = Color.LIGHT_BORDER
            self.text = "#1f2937"
            self.text_secondary = "#4b5563"
            self.text_muted = "#9ca3af"
        
        self.primary = Color.PRIMARY
        self.secondary = Color.SECONDARY
        self.success = Color.SUCCESS
        self.warning = Color.WARNING
        self.error = Color.ERROR
        self.info = Color.INFO


def format_time(timestamp: float) -> str:
    """Format timestamp"""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return "just now"
    elif diff < 3600:
        mins = int(diff / 60)
        return f"{mins}m ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours}h ago"
    else:
        import datetime
        return datetime.datetime.fromtimestamp(timestamp).strftime("%b %d")


def format_size(bytes: int) -> str:
    """Format file size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}PB"


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate text"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def align_text(text: str, width: int, align: str = "left") -> str:
    """Align text within width"""
    text_len = len(text)
    if text_len >= width:
        return text[:width]
    
    if align == "left":
        return text + " " * (width - text_len)
    elif align == "right":
        return " " * (width - text_len) + text
    elif align == "center":
        left = (width - text_len) // 2
        right = width - text_len - left
        return " " * left + text + " " * right
    else:
        return text


def center(text: str, width: int) -> str:
    """Center text"""
    padding = max(0, (width - len(text)) // 2)
    return " " * padding + text


def pad_left(text: str, width: int) -> str:
    """Pad text to left"""
    return text.rjust(width)


def pad_right(text: str, width: int) -> str:
    """Pad text to right"""
    return text.ljust(width)


def git_status(cwd: str = None) -> dict:
    """Get git status"""
    if cwd is None:
        cwd = os.getcwd()
    
    result = {
        "is_repo": False,
        "branch": "main",
        "changes": [],
        "staged": [],
        "untracked": [],
    }
    
    try:
        is_git = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd, capture_output=True, text=True
        )
        
        if is_git.returncode != 0:
            return result
        
        result["is_repo"] = True
        
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, capture_output=True, text=True
        )
        result["branch"] = branch.stdout.strip() or "main"
        
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True
        )
        
        if status.stdout:
            for line in status.stdout.strip().split("\n"):
                if len(line) >= 3:
                    code = line[:2]
                    path = line[3:]
                    
                    result["changes"].append(path)
                    
                    if code[0] in ["M", "A", "D"]:
                        result["staged"].append(path)
                    if code[1] == "?":
                        result["untracked"].append(path)
    
    except:
        pass
    
    return result


def get_git_diff(cwd: str = None, file: str = None) -> str:
    """Get git diff"""
    if cwd is None:
        cwd = os.getcwd()
    
    cmd = ["git", "diff"]
    if file:
        cmd.append(file)
    
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True
        )
        return result.stdout or result.stderr
    except:
        return ""