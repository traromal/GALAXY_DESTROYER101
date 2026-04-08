"""Components package - reusable UI components"""

from typing import Any, Optional, List, Dict, Callable
from dataclasses import dataclass
from enum import Enum


class ComponentType(Enum):
    TEXT = "text"
    BOX = "box"
    BUTTON = "button"
    INPUT = "input"
    LIST = "list"
    TABLE = "table"
    PROGRESS = "progress"
    SPINNER = "spinner"


@dataclass
class Component:
    """Base component"""
    type: ComponentType
    props: Dict[str, Any]
    children: List['Component'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class Text(Component):
    """Text component"""
    def __init__(self, content: str, bold: bool = False, color: str = None, **props):
        super().__init__(
            type=ComponentType.TEXT,
            props={"content": content, "bold": bold, "color": color, **props}
        )


class Box(Component):
    """Box/frame component"""
    def __init__(self, children: List[Component] = None, border: bool = True, 
                 padding: int = 1, title: str = None, **props):
        super().__init__(
            type=ComponentType.BOX,
            props={"border": border, "padding": padding, "title": title, **props},
            children=children or []
        )


class Button(Component):
    """Button component"""
    def __init__(self, label: str, on_click: Callable = None, disabled: bool = False, **props):
        super().__init__(
            type=ComponentType.BUTTON,
            props={"label": label, "on_click": on_click, "disabled": disabled, **props}
        )


class Input(Component):
    """Input component"""
    def __init__(self, value: str = "", placeholder: str = "", on_change: Callable = None, **props):
        super().__init__(
            type=ComponentType.INPUT,
            props={"value": value, "placeholder": placeholder, "on_change": on_change, **props}
        )


class List(Component):
    """List component"""
    def __init__(self, items: List[str] = None, selected: int = None, on_select: Callable = None, **props):
        super().__init__(
            type=ComponentType.LIST,
            props={"items": items or [], "selected": selected, "on_select": on_select, **props}
        )


class Table(Component):
    """Table component"""
    def __init__(self, headers: List[str] = None, rows: List[List[str]] = None, **props):
        super().__init__(
            type=ComponentType.TABLE,
            props={"headers": headers or [], "rows": rows or [], **props}
        )


class Progress(Component):
    """Progress bar component"""
    def __init__(self, value: float = 0, max: float = 100, show_label: bool = True, **props):
        super().__init__(
            type=ComponentType.PROGRESS,
            props={"value": value, "max": max, "show_label": show_label, **props}
        )


class Spinner(Component):
    """Spinner component"""
    def __init__(self, message: str = "Loading...", **props):
        super().__init__(
            type=ComponentType.SPINNER,
            props={"message": message, **props}
        )


class Renderable:
    """Interface for renderable components"""
    
    def render(self, width: int, height: int) -> List[str]:
        raise NotImplementedError


def render_component(comp: Component, width: int, height: int) -> List[str]:
    """Render a component to strings"""
    if comp.type == ComponentType.TEXT:
        return [comp.props.get("content", "")]
    elif comp.type == ComponentType.BOX:
        return _render_box(comp, width, height)
    elif comp.type == ComponentType.LIST:
        return _render_list(comp, width)
    elif comp.type == ComponentType.PROGRESS:
        return _render_progress(comp, width)
    elif comp.type == ComponentType.SPINNER:
        return [comp.props.get("message", "Loading...")]
    return []


def _render_box(box: Box, width: int, height: int) -> List[str]:
    """Render a box component"""
    lines = []
    
    if box.props.get("border", True):
        lines.append("┌" + "─" * (width - 2) + "┐")
        for i in range(height - 2):
            lines.append("│" + " " * (width - 2) + "│")
        lines.append("└" + "─" * (width - 2) + "┘")
    else:
        for i in range(height):
            lines.append(" " * width)
    
    return lines


def _render_list(lst: List, width: int) -> List[str]:
    """Render a list component"""
    lines = []
    items = lst.props.get("items", [])
    selected = lst.props.get("selected")
    
    for i, item in enumerate(items):
        prefix = "► " if i == selected else "  "
        lines.append(prefix + item[:width - 2])
    
    return lines


def _render_progress(prog: Progress, width: int) -> List[str]:
    """Render a progress bar"""
    value = prog.props.get("value", 0)
    max_val = prog.props.get("max", 100)
    show_label = prog.props.get("show_label", True)
    
    percentage = min(1.0, value / max_val)
    filled = int((width - 4) * percentage)
    
    bar = "[" + "█" * filled + " " * (width - 4 - filled) + "]"
    
    if show_label:
        label = f" {int(percentage * 100)}%"
        bar = bar[:width - len(label)] + label
    
    return [bar]


class Layout:
    """Layout system for positioning components"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._components: List[tuple] = []
    
    def add(self, comp: Component, x: int, y: int, w: int = None, h: int = None):
        w = w or (self.width - x)
        h = h or (self.height - y)
        self._components.append((comp, x, y, w, h))
    
    def render(self) -> List[str]:
        output = [[" " for _ in range(self.width)] for _ in range(self.height)]
        
        for comp, x, y, w, h in self._components:
            lines = render_component(comp, w, h)
            for i, line in enumerate(lines):
                if y + i < self.height:
                    for j, char in enumerate(line):
                        if x + j < self.width:
                            output[y + i][x + j] = char
        
        return ["".join(row) for row in output]