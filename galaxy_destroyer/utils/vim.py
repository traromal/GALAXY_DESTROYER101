"""Vim mode - text editing in terminal"""

from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum


class VimMode(Enum):
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    LINE_VISUAL = "line_visual"
    COMMAND = "command"


class VimRegister:
    """Vim register for storing text"""
    def __init__(self):
        self._registers: Dict[str, str] = {'"': ""}
        self._default = '"'
    
    def set(self, name: str, value: str):
        self._registers[name] = value
    
    def get(self, name: str = None) -> str:
        return self._registers.get(name or self._default, "")
    
    def append(self, value: str):
        current = self.get()
        self.set(self._default, current + value)


@dataclass
class VimState:
    """Vim editing state"""
    mode: VimMode = VimMode.NORMAL
    register: VimRegister = None
    count: int = 1
    operator: Optional[str] = None
    motion: Optional[str] = None
    last_operator: Optional[str] = None
    last_motion: Optional[str] = None
    last_command: Optional[str] = None
    search_pattern: str = ""
    last_search: str = ""
    mark_positions: Dict[str, int] = None
    
    def __post_init__(self):
        if self.register is None:
            self.register = VimRegister()
        if self.mark_positions is None:
            self.mark_positions = {}


class VimEditor:
    """Vim-style text editor"""
    
    def __init__(self):
        self.state = VimState()
        self._operators = {
            'd': self._op_delete,
            'c': self._op_change,
            'y': self._op_yank,
            'g': self._op_g,
            '>': self._op_indent,
            '<': self._op_dedent,
            '!': self._op_filter,
        }
        self._motions = {
            'h': self._move_left,
            'j': self._move_down,
            'k': self._move_up,
            'l': self._move_right,
            'w': self._move_word_forward,
            'b': self._move_word_back,
            'e': self._move_word_end,
            '0': self._move_line_start,
            '$': self._move_line_end,
            'gg': self._move_buffer_start,
            'G': self._move_buffer_end,
            'f': self._move_find,
            'F': self._move_find_back,
            't': self._move_find_before,
            'T': self._move_find_before_back,
            '/': self._search_forward,
            '?': self._search_backward,
            'n': self._search_next,
            'N': self._search_prev,
        }
        self._insert_commands = {
            'i': self._enter_insert,
            'I': self._enter_insert_bol,
            'a': self._enter_insert_after,
            'A': self._enter_insert_eol,
            'o': self._open_line_below,
            'O': self._open_line_above,
            's': self._substitute_char,
            'S': self._substitute_line,
            'c': self._change,
            'R': self._enter_replace,
        }
    
    def handle_key(self, key: str, buffer: str, cursor: int) -> tuple[str, int]:
        """Handle a key press, return new buffer and cursor"""
        mode = self.state.mode
        
        if mode == VimMode.NORMAL:
            return self._handle_normal(key, buffer, cursor)
        elif mode == VimMode.INSERT:
            return self._handle_insert(key, buffer, cursor)
        elif mode == VimMode.VISUAL:
            return self._handle_visual(key, buffer, cursor)
        
        return buffer, cursor
    
    def _handle_normal(self, key: str, buffer: str, cursor: int) -> tuple[str, int]:
        """Handle normal mode key"""
        if key in self._operators:
            self.state.operator = key
            return buffer, cursor
        
        if key in self._motions:
            motion_fn = self._motions[key]
            new_cursor = motion_fn(buffer, cursor, self.state.count)
            if self.state.operator:
                return self._execute_operator(buffer, cursor, new_cursor)
            return buffer, new_cursor
        
        if key in self._insert_commands:
            insert_fn = self._insert_commands[key]
            return insert_fn(buffer, cursor)
        
        if key == 'x':
            if cursor < len(buffer):
                buffer = buffer[:cursor] + buffer[cursor+1:]
            return buffer, cursor
        
        if key == 'p':
            text = self.state.register.get()
            buffer = buffer[:cursor] + text + buffer[cursor:]
            cursor += len(text)
            return buffer, cursor
        
        if key == 'P':
            text = self.state.register.get()
            buffer = text + buffer
            cursor += len(text)
            return buffer, cursor
        
        if key == 'u':
            return buffer, cursor
        
        if key == 'Ctrl+r':
            return buffer, cursor
        
        if key == '.':
            if self.state.last_command:
                pass
            return buffer, cursor
        
        if key == '~':
            if cursor < len(buffer):
                char = buffer[cursor]
                if char.islower():
                    char = char.upper()
                elif char.isupper():
                    char = char.lower()
                buffer = buffer[:cursor] + char + buffer[cursor+1:]
            return buffer, cursor
        
        if key == 'Escape':
            self.state.operator = None
            return buffer, cursor
        
        return buffer, cursor
    
    def _handle_insert(self, key: str, buffer: str, cursor: int) -> tuple[str, int]:
        """Handle insert mode key"""
        if key == 'Escape':
            self.state.mode = VimMode.NORMAL
            return buffer, max(0, cursor - 1)
        
        if key == 'backspace':
            if cursor > 0:
                buffer = buffer[:cursor-1] + buffer[cursor:]
                cursor -= 1
            return buffer, cursor
        
        if key == 'enter':
            buffer = buffer[:cursor] + '\n' + buffer[cursor:]
            cursor += 1
            return buffer, cursor
        
        if key == 'tab':
            buffer = buffer[:cursor] + '    ' + buffer[cursor:]
            cursor += 4
            return buffer, cursor
        
        if key == 'Ctrl+w':
            words = buffer[:cursor].split()
            if words:
                buffer = buffer[:cursor - len(words[-1])] + buffer[cursor:]
                cursor -= len(words[-1])
            return buffer, cursor
        
        if key == 'Ctrl+u':
            buffer = buffer[cursor:]
            cursor = 0
            return buffer, cursor
        
        if len(key) == 1:
            buffer = buffer[:cursor] + key + buffer[cursor:]
            cursor += 1
        
        return buffer, cursor
    
    def _handle_visual(self, key: str, buffer: str, cursor: int) -> tuple[str, int]:
        """Handle visual mode key"""
        if key == 'Escape':
            self.state.mode = VimMode.NORMAL
            return buffer, cursor
        
        if key == 'd' or key == 'y':
            self.state.operator = key
            return self._execute_operator(buffer, cursor, cursor)
        
        return buffer, cursor
    
    def _execute_operator(self, buffer: str, cursor: int, end_cursor: int) -> tuple[str, int]:
        """Execute operator on range"""
        op = self.state.operator
        self.state.operator = None
        
        if op == 'd':
            deleted = buffer[cursor:end_cursor]
            self.state.register.set('"', deleted)
            buffer = buffer[:cursor] + buffer[end_cursor:]
            return buffer, cursor
        
        if op == 'y':
            yanked = buffer[cursor:end_cursor]
            self.state.register.set('"', yanked)
            return buffer, cursor
        
        if op == 'c':
            deleted = buffer[cursor:end_cursor]
            self.state.register.set('"', deleted)
            buffer = buffer[:cursor] + buffer[end_cursor:]
            self.state.mode = VimMode.INSERT
            return buffer, cursor
        
        return buffer, cursor
    
    def _enter_insert(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        return buffer, cursor
    
    def _enter_insert_bol(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        while cursor > 0 and buffer[cursor-1] != '\n':
            cursor -= 1
        return buffer, cursor
    
    def _enter_insert_after(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        if cursor < len(buffer):
            cursor += 1
        return buffer, cursor
    
    def _enter_insert_eol(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        while cursor < len(buffer) and buffer[cursor] != '\n':
            cursor += 1
        return buffer, cursor
    
    def _open_line_below(self, buffer: str, cursor: int) -> tuple[str, int]:
        line_end = cursor
        while line_end < len(buffer) and buffer[line_end] != '\n':
            line_end += 1
        buffer = buffer[:line_end] + '\n' + buffer[line_end:]
        self.state.mode = VimMode.INSERT
        return buffer, cursor + 1
    
    def _open_line_above(self, buffer: str, cursor: int) -> tuple[str, int]:
        line_start = cursor
        while line_start > 0 and buffer[line_start-1] != '\n':
            line_start -= 1
        buffer = buffer[:line_start] + '\n' + buffer[line_start:]
        self.state.mode = VimMode.INSERT
        return buffer, cursor
    
    def _substitute_char(self, buffer: str, cursor: int) -> tuple[str, int]:
        if cursor < len(buffer):
            buffer = buffer[:cursor] + buffer[cursor+1:]
        self.state.mode = VimMode.INSERT
        return buffer, cursor
    
    def _substitute_line(self, buffer: str, cursor: int) -> tuple[str, int]:
        line_start = cursor
        while line_start > 0 and buffer[line_start-1] != '\n':
            line_start -= 1
        line_end = cursor
        while line_end < len(buffer) and buffer[line_end] != '\n':
            line_end += 1
        buffer = buffer[:line_start] + buffer[line_end:]
        self.state.mode = VimMode.INSERT
        return buffer, line_start
    
    def _change(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        return buffer, cursor
    
    def _enter_replace(self, buffer: str, cursor: int) -> tuple[str, int]:
        self.state.mode = VimMode.INSERT
        return buffer, cursor
    
    def _move_left(self, buffer: str, cursor: int, count: int) -> int:
        return max(0, cursor - count)
    
    def _move_right(self, buffer: str, cursor: int, count: int) -> int:
        return min(len(buffer), cursor + count)
    
    def _move_down(self, buffer: str, cursor: int, count: int) -> int:
        lines = buffer.split('\n')
        current_line = buffer[:cursor].count('\n')
        target = min(len(lines) - 1, current_line + count)
        line_start = 0
        for i in range(target):
            line_start = buffer.find('\n', line_start) + 1
        return line_start
    
    def _move_up(self, buffer: str, cursor: int, count: int) -> int:
        lines = buffer.split('\n')
        current_line = buffer[:cursor].count('\n')
        target = max(0, current_line - count)
        line_start = 0
        for i in range(target):
            line_start = buffer.find('\n', line_start) + 1
        return line_start
    
    def _move_word_forward(self, buffer: str, cursor: int, count: int) -> int:
        i = cursor
        while i < len(buffer) and buffer[i] in ' \t':
            i += 1
        while i < len(buffer) and buffer[i] not in ' \t\n':
            i += 1
        return i
    
    def _move_word_back(self, buffer: str, cursor: int, count: int) -> int:
        i = cursor - 1
        while i >= 0 and buffer[i] in ' \t':
            i -= 1
        while i >= 0 and buffer[i] not in ' \t\n':
            i -= 1
        return max(0, i + 1)
    
    def _move_word_end(self, buffer: str, cursor: int, count: int) -> int:
        i = cursor
        while i < len(buffer) and buffer[i] in ' \t':
            i += 1
        while i < len(buffer) and buffer[i] not in ' \t\n':
            i += 1
        return max(0, i - 1)
    
    def _move_line_start(self, buffer: str, cursor: int, count: int) -> int:
        line_start = buffer.rfind('\n', 0, cursor)
        return line_start + 1 if line_start >= 0 else 0
    
    def _move_line_end(self, buffer: str, cursor: int, count: int) -> int:
        next_newline = buffer.find('\n', cursor)
        return next_newline if next_newline >= 0 else len(buffer)
    
    def _move_buffer_start(self, buffer: str, cursor: int, count: int) -> int:
        return 0
    
    def _move_buffer_end(self, buffer: str, cursor: int, count: int) -> int:
        return len(buffer)
    
    def _move_find(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _move_find_back(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _move_find_before(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _move_find_before_back(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _search_forward(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _search_backward(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _search_next(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _search_prev(self, buffer: str, cursor: int, count: int) -> int:
        return cursor
    
    def _op_delete(self, buffer: str, start: int, end: int) -> str:
        return buffer[:start] + buffer[end:]
    
    def _op_change(self, buffer: str, start: int, end: int) -> str:
        return buffer[:start] + buffer[end:]
    
    def _op_yank(self, buffer: str, start: int, end: int) -> str:
        return buffer
    
    def _op_g(self, buffer: str, start: int, end: int) -> str:
        return buffer
    
    def _op_indent(self, buffer: str, start: int, end: int) -> str:
        return buffer
    
    def _op_dedent(self, buffer: str, start: int, end: int) -> str:
        return buffer
    
    def _op_filter(self, buffer: str, start: int, end: int) -> str:
        return buffer
    
    def get_mode(self) -> VimMode:
        return self.state.mode
    
    def set_mode(self, mode: VimMode):
        self.state.mode = mode
    
    def is_insert_mode(self) -> bool:
        return self.state.mode == VimMode.INSERT
    
    def is_visual_mode(self) -> bool:
        return self.state.mode in (VimMode.VISUAL, VimMode.LINE_VISUAL)