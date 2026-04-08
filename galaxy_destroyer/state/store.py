"""State management - App state, store, selectors"""

import os
import json
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class AppMode(Enum):
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    COMMAND = "command"
    REPL = "repl"


@dataclass
class UserInfo:
    """User information"""
    id: str = ""
    email: str = ""
    name: str = ""
    organization: str = ""
    subscription_type: str = "free"


@dataclass
class SessionInfo:
    """Session information"""
    id: str = ""
    project_path: str = ""
    started_at: float = field(default_factory=time.time)
    message_count: int = 0
    tool_calls: int = 0


@dataclass
class AppState:
    """Main application state"""
    mode: AppMode = AppMode.NORMAL
    cwd: str = field(default_factory=os.getcwd)
    input_buffer: str = ""
    output_buffer: List[str] = field(default_factory=list)
    cursor_pos: int = 0
    scroll_offset: int = 0
    
    history: List[str] = field(default_factory=list)
    history_index: int = -1
    
    is_loading: bool = False
    error: Optional[str] = None
    
    user: UserInfo = field(default_factory=UserInfo)
    session: SessionInfo = field(default_factory=SessionInfo)
    
    model: str = "claude-opus-4-5-20251114"
    temperature: float = 1.0
    stream: bool = True
    color: bool = True
    
    messages: List[Dict] = field(default_factory=list)
    
    selected_tool: Optional[str] = None
    active_tools: List[str] = field(default_factory=list)
    
    vim_mode: str = "normal"
    vim_registers: Dict[str, str] = field(default_factory=dict)
    
    keybindings: Dict[str, Callable] = field(default_factory=dict)
    
    config: Dict[str, Any] = field(default_factory=dict)
    
    terminal_size: tuple = (80, 24)


class Store:
    """Simple state store with subscriptions"""
    
    def __init__(self, initial_state: Optional[AppState] = None):
        self._state = initial_state or AppState()
        self._subscribers: List[Callable[[AppState], None]] = []
        self._listeners: Dict[str, List[Callable]] = {}
    
    def get_state(self) -> AppState:
        """Get current state"""
        return self._state
    
    def set_state(self, state: AppState) -> None:
        """Set entire state"""
        self._state = state
        self._notify()
    
    def update(self, **kwargs) -> None:
        """Update state fields"""
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        self._notify()
    
    def subscribe(self, callback: Callable[[AppState], None]) -> None:
        """Subscribe to state changes"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable[[AppState], None]) -> None:
        """Unsubscribe from state changes"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def on(self, event: str, callback: Callable) -> None:
        """Register event listener"""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit event to listeners"""
        if event in self._listeners:
            for callback in self._listeners[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    pass
    
    def _notify(self) -> None:
        """Notify all subscribers"""
        for callback in self._subscribers:
            try:
                callback(self._state)
            except Exception as e:
                pass


_store = Store()


def get_store() -> Store:
    """Get global store"""
    return _store


def get_state() -> AppState:
    """Get current state"""
    return _store.get_state()


def update_state(**kwargs) -> None:
    """Update state fields"""
    _store.update(**kwargs)


def subscribe(callback: Callable[[AppState], None]) -> None:
    """Subscribe to state changes"""
    _store.subscribe(callback)


def on(event: str, callback: Callable) -> None:
    """Register event"""
    _store.on(event, callback)


def emit(event: str, *args, **kwargs) -> None:
    """Emit event"""
    _store.emit(event, *args, **kwargs)


class Selectors:
    """State selectors"""
    
    @staticmethod
    def get_mode(state: AppState) -> AppMode:
        return state.mode
    
    @staticmethod
    def get_cwd(state: AppState) -> str:
        return state.cwd
    
    @staticmethod
    def get_input(state: AppState) -> str:
        return state.input_buffer
    
    @staticmethod
    def get_output(state: AppState) -> List[str]:
        return state.output_buffer
    
    @staticmethod
    def get_messages(state: AppState) -> List[Dict]:
        return state.messages
    
    @staticmethod
    def get_error(state: AppState) -> Optional[str]:
        return state.error
    
    @staticmethod
    def is_loading(state: AppState) -> bool:
        return state.is_loading
    
    @staticmethod
    def get_model(state: AppState) -> str:
        return state.model
    
    @staticmethod
    def get_user(state: AppState) -> UserInfo:
        return state.user
    
    @staticmethod
    def get_session(state: AppState) -> SessionInfo:
        return state.session
    
    @staticmethod
    def get_history(state: AppState) -> List[str]:
        return state.history
    
    @staticmethod
    def get_config(state: AppState) -> Dict:
        return state.config