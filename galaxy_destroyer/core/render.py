"""Terminal rendering system - core of the TUI"""

import os
import sys
import io
from typing import Optional
from dataclasses import dataclass
from enum import Enum

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class Align(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def get_terminal_size() -> tuple[int, int]:
    """Get terminal width and height"""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24


def clear_screen():
    """Clear the terminal screen"""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def move_cursor(x: int, y: int):
    """Move cursor to position (1-indexed)"""
    sys.stdout.write(f"\033[{y};{x}H")
    sys.stdout.flush()


def save_cursor():
    sys.stdout.write("\033[s")
    sys.stdout.flush()


def restore_cursor():
    sys.stdout.write("\u001b[u")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def scroll_up(lines: int = 1):
    sys.stdout.write(f"\033[{lines}S")
    sys.stdout.flush()


def scroll_down(lines: int = 1):
    sys.stdout.write(f"\033[{lines}T")
    sys.stdout.flush()


def erase_display():
    sys.stdout.write("\033[2J")
    sys.stdout.flush()


def erase_line():
    sys.stdout.write("\033[2K")
    sys.stdout.flush()


def write(text: str):
    sys.stdout.write(text)
    sys.stdout.flush()


def write_line(text: str = ""):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def style(text: str, bold: bool = False, italic: bool = False, 
          underline: bool = False, color: Optional[str] = None,
          bg_color: Optional[str] = None, dim: bool = False) -> str:
    codes = []
    if bold:
        codes.append("1")
    if italic:
        codes.append("3")
    if underline:
        codes.append("4")
    if dim:
        codes.append("2")
    
    color_codes = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "reset": "0", "gray": "90", "bright_red": "91", "bright_green": "92",
        "bright_yellow": "93", "bright_blue": "94", "bright_magenta": "95",
        "bright_cyan": "96", "bright_white": "97",
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


@dataclass
class BorderStyle:
    vertical: str = "│"
    horizontal: str = "─"
    top_left: str = "┌"
    top_right: str = "┐"
    bottom_left: str = "└"
    bottom_right: str = "┘"


DOUBLE_BORDER = BorderStyle(
    vertical="║", horizontal="═", top_left="╔", top_right="╗",
    bottom_left="╚", bottom_right="╝"
)

ROUNDED_BORDER = BorderStyle(
    vertical="│", horizontal="─", top_left="╭", top_right="╮",
    bottom_left="╰", bottom_right="╯"
)


def render_box(content: list[str], width: int, height: int, 
               border: BorderStyle = BorderStyle(),
               padding: int = 1) -> list[str]:
    """Render content inside a bordered box"""
    lines = []
    top_border = border.top_left + border.horizontal * (width - 2) + border.top_right
    bottom_border = border.bottom_left + border.horizontal * (width - 2) + border.bottom_right
    
    lines.append(top_border)
    
    for i in range(height - 2):
        if i < len(content):
            padded = content[i].ljust(width - 2)
            lines.append(border.vertical + padded + border.vertical)
        else:
            lines.append(border.vertical + " " * (width - 2) + border.vertical)
    
    lines.append(bottom_border)
    return lines


def word_wrap(text: str, width: int) -> list[str]:
    """Wrap text to fit within width"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


def truncate(text: str, width: int, suffix: str = "...") -> str:
    """Truncate text to fit width"""
    if len(text) <= width:
        return text
    return text[:width - len(suffix)] + suffix


def align_text(text: str, width: int, align: Align = Align.LEFT) -> str:
    """Align text within width"""
    text = text[:width]
    if align == Align.LEFT:
        return text.ljust(width)
    elif align == Align.CENTER:
        return text.center(width)
    elif align == Align.RIGHT:
        return text.rjust(width)
    return text