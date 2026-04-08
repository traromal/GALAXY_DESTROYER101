"""Components - UI components for TUI"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Button:
    """Button component"""
    text: str
    color: str = "blue"
    hover_color: str = "cyan"
    selected: bool = False
    
    def render(self) -> str:
        from core.render import style
        bg = self.hover_color if self.selected else self.color
        return style(f" {self.text} ", bg_color=bg, color="white", bold=True)


@dataclass
class ListItem:
    """List item component"""
    text: str
    icon: str = "•"
    color: str = "white"
    selected: bool = False
    indent: int = 0
    
    def render(self) -> str:
        from core.render import style
        prefix = " " * self.indent + style(self.icon, color=self.color)
        if self.selected:
            prefix += style(" ▶", color="cyan")
        return f"{prefix} {self.text}"


class Menu:
    """Menu component"""
    
    def __init__(self, title: str, items: List[str]):
        self.title = title
        self.items = items
        self.selected = 0
    
    def select_next(self):
        self.selected = (self.selected + 1) % len(self.items)
    
    def select_prev(self):
        self.selected = (self.selected - 1) % len(self.items)
    
    def render(self) -> List[str]:
        from core.render import style
        
        lines = []
        lines.append(style(f" ╭─ {self.title} ────╮", color="cyan", bold=True))
        
        for i, item in enumerate(self.items):
            icon = "▶" if i == self.selected else " "
            color = "cyan" if i == self.selected else "white"
            lines.append(style(f" │{icon} {item}", color=color))
        
        lines.append(style(f" ╰─{'─' * len(self.title)}───╯", color="cyan", bold=True))
        
        return lines


class Table:
    """Table component"""
    
    def __init__(self, columns: List[str], rows: List[List[str]]):
        self.columns = columns
        self.rows = rows
        self.col_widths = [len(c) for c in columns]
        
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(self.col_widths):
                    self.col_widths[i] = max(self.col_widths[i], len(cell))
    
    def render(self) -> List[str]:
        from core.render import style
        
        lines = []
        
        header = " │ ".join(
            c.ljust(w) for c, w in zip(self.columns, self.col_widths)
        )
        lines.append(style(f" {header} ", bg_color="blue", color="white", bold=True))
        
        sep = "─" * (len(header) + 2)
        lines.append(style(sep, color="gray"))
        
        for row in self.rows:
            cells = [c.ljust(w) if i < len(self.col_widths) else c 
                    for i, c in enumerate(row)]
            lines.append(" │ ".join(cells))
        
        return lines


class Panel:
    """Panel component"""
    
    def __init__(self, title: str, content: List[str], 
                 width: int = 30, border: str = "cyan"):
        self.title = title
        self.content = content
        self.width = width
        self.border = border
    
    def render(self) -> List[str]:
        from core.render import style, word_wrap
        
        lines = []
        
        title_line = f" {self.title} "
        if len(title_line) < self.width - 2:
            title_line = title_line.center(self.width - 2, "─")
        
        lines.append(style("╭" + title_line + "╮", color=self.border, bold=True))
        
        for line in self.content:
            wrapped = word_wrap(line, self.width - 4)
            for w in wrapped[:self.width - 6]:
                lines.append(style("│ ", color=self.border) + w.ljust(self.width - 4))
        
        while len(lines) < 5:
            lines.append(style("│", color=self.border) + " " * (self.width - 2))
        
        lines.append(style("╰" + "─" * (self.width - 2) + "╯", color=self.border, bold=True))
        
        return lines


class Modal:
    """Modal dialog component"""
    
    def __init__(self, title: str, message: str, 
                 buttons: List[str] = None):
        self.title = title
        self.message = message
        self.buttons = buttons or ["OK"]
        self.selected = 0
    
    def select_next(self):
        self.selected = (self.selected + 1) % len(self.buttons)
    
    def select_prev(self):
        self.selected = (self.selected - 1) % len(self.buttons)
    
    def render(self) -> List[str]:
        from core.render import style, word_wrap
        
        lines = []
        
        title_line = f" {self.title} "
        width = 50
        title_line = title_line.center(width - 2, "─")
        
        lines.append(style("╭" + title_line + "╮", color="cyan", bold=True))
        lines.append(style("│", color="cyan") + " " * (width - 2) + style("│", color="cyan"))
        
        for line in word_wrap(self.message, width - 4):
            lines.append(style("│ ", color="cyan") + line.ljust(width - 4) + style(" │", color="cyan"))
        
        lines.append(style("│", color="cyan") + " " * (width - 2) + style("│", color="cyan"))
        
        btn_str = " ".join(
            style(f"[{b}]", color="cyan" if i == self.selected else "gray")
            for i, b in enumerate(self.buttons)
        )
        lines.append(style("│ ", color="cyan") + btn_str.center(width - 4) + style(" │", color="cyan"))
        
        lines.append(style("╰" + "─" * (width - 2) + "╯", color="cyan", bold=True))
        
        return lines


class Toast:
    """Toast notification component"""
    
    def __init__(self, message: str, kind: str = "info"):
        self.message = message
        self.kind = kind
    
    def render(self) -> str:
        from core.render import style
        
        color_map = {
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "info": "cyan",
        }
        
        icon_map = {
            "success": "✓",
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ",
        }
        
        icon = icon_map.get(self.kind, "ℹ")
        color = color_map.get(self.kind, "white")
        
        return style(f" {icon} {self.message} ", color=color, bold=True)


class StatusBar:
    """Status bar component"""
    
    def __init__(self, items: List[str]):
        self.items = items
    
    def render(self) -> str:
        from core.render import style
        
        parts = []
        
        for item in self.items:
            if isinstance(item, tuple):
                icon, text, color = item[0], item[1], item[2] if len(item) > 2 else "white"
                parts.append(style(icon, color=color) + " " + text)
            else:
                parts.append(item)
        
        return " │ ".join(parts)


class Breadcrumb:
    """Breadcrumb navigation"""
    
    def __init__(self, path: str):
        self.path = path
        self.parts = path.split("/")
    
    def render(self) -> str:
        from core.render import style
        
        parts = []
        
        for i, part in enumerate(self.parts):
            if i > 0:
                parts.append(style(" / ", color="gray", dim=True))
            if i == len(self.parts) - 1:
                parts.append(style(part, color="cyan", bold=True))
            else:
                parts.append(part)
        
        return "".join(parts)


class TabBar:
    """Tab bar component"""
    
    def __init__(self, tabs: List[str]):
        self.tabs = tabs
        self.active = 0
    
    def set_active(self, index: int):
        if 0 <= index < len(self.tabs):
            self.active = index
    
    def render(self) -> str:
        from core.render import style
        
        parts = []
        
        for i, tab in enumerate(self.tabs):
            if i == self.active:
                parts.append(style(f"[{tab}]", color="cyan", bold=True))
            else:
                parts.append(style(f"[{tab}]", color="gray"))
        
        return " ".join(parts)


class Input:
    """Input field component"""
    
    def __init__(self, placeholder: str = "", value: str = ""):
        self.placeholder = placeholder
        self.value = value
        self.cursor = len(value)
    
    def render(self) -> str:
        from core.render import style
        
        prompt = style(">", color="green", bold=True)
        
        text = self.value or style(self.placeholder, color="gray", dim=True)
        
        return f"{prompt} {text}"


class Dropdown:
    """Dropdown component"""
    
    def __init__(self, options: List[str], selected: int = 0):
        self.options = options
        self.selected = selected
        self.open = False
    
    def toggle(self):
        self.open = not self.open
    
    def select(self, index: int):
        if 0 <= index < len(self.options):
            self.selected = index
            self.open = False
    
    def render(self) -> str:
        from core.render import style
        
        text = self.options[self.selected]
        
        if self.open:
            lines = [style(f"▾ {text}", color="cyan", bold=True)]
            for i, opt in enumerate(self.options):
                icon = "▶" if i == self.selected else " "
                lines.append(style(f"  {icon} {opt}", color="cyan" if i == self.selected else "white"))
            return "\n".join(lines)
        else:
            return style(f"▾ {text}", color="white")


class Progress:
    """Progress bar component"""
    
    def __init__(self, value: float, width: int = 20):
        self.value = max(0, min(1, value))
        self.width = width
    
    def render(self) -> str:
        from core.render import style
        
        filled = int(self.width * self.value)
        bar = "█" * filled + "░" * (self.width - filled)
        percent = int(self.value * 100)
        
        return style(f"[{bar}] {percent}%", color="cyan")


class Badge:
    """Badge component"""
    
    def __init__(self, text: str, color: str = "blue"):
        self.text = text
        self.color = color
    
    def render(self) -> str:
        from core.render import style
        return style(f" {self.text} ", bg_color=self.color, color="white")


class Tag:
    """Tag component"""
    
    def __init__(self, text: str, color: str = "gray"):
        self.text = text
        self.color = color
    
    def render(self) -> str:
        from core.render import style
        return style(f"{self.text}", color=self.color)


class Divider:
    """Divider component"""
    
    def __init__(self, style: str = "line"):
        self.style = style
    
    def render(self) -> str:
        from core.render import style, get_terminal_size
        width = get_terminal_size()[0]
        
        if self.style == "line":
            return style("─" * width, color="gray", dim=True)
        elif self.style == "double":
            return style("═" * width, color="gray", dim=True)
        elif self.style == "dotted":
            return style("·" * width, color="gray", dim=True)
        else:
            return style("─" * width, color="gray", dim=True)


class Spacer:
    """Spacer component"""
    
    def __init__(self, height: int = 1):
        self.height = height
    
    def render(self) -> str:
        return "\n" * self.height