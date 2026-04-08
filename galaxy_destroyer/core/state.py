"""State management system"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum
import time


class Color(Enum):
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


@dataclass
class Context:
    """Application context - stores all state"""
    cwd: str = ""
    messages: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    session_id: str = ""
    auth_token: Optional[str] = None
    model: str = "qwen2.5-coder"
    backend: str = "opencode"
    stream: bool = True
    color: bool = True
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content, "timestamp": time.time()})
    
    def add_tool_result(self, tool_name: str, result: Any):
        self.messages.append({"role": "tool", "tool": tool_name, "result": result, "timestamp": time.time()})


@dataclass
class State:
    """Mutable application state"""
    input_buffer: str = ""
    output_buffer: list = field(default_factory=list)
    cursor_pos: int = 0
    scroll_offset: int = 0
    history: list = field(default_factory=list)
    history_index: int = -1
    mode: str = "normal"  # normal, insert, visual, command
    selected_tool: Optional[str] = None
    is_loading: bool = False
    error: Optional[str] = None
    
    def push_output(self, line: str):
        self.output_buffer.append(line)
    
    def clear_output(self):
        self.output_buffer.clear()
    
    def add_to_history(self, cmd: str):
        if cmd.strip():
            self.history.append(cmd)
        self.history_index = len(self.history)


class Component:
    """Base class for UI components"""
    def render(self, width: int, height: int) -> list[str]:
        return []
    
    def handle_key(self, key: str) -> Optional[str]:
        return None


class Callback:
    def __init__(self, fn: Callable):
        self.fn = fn
        self._enabled = True
    
    def enable(self):
        self._enabled = True
    
    def disable(self):
        self._enabled = False
    
    def call(self, *args, **kwargs):
        if self._enabled:
            return self.fn(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)