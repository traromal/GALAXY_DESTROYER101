"""Configuration management system"""

import json
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


DEFAULT_CONFIG = {
    "model": "qwen2.5-coder",
    "backend": "opencode",
    "api_key": "",
    "color": True,
    "stream": True,
    "auto_save": True,
    "vim_mode": False,
    "theme": "default",
    "font_size": 14,
    "max_tokens": 4096,
    "temperature": 0.7,
    "tools": {
        "enabled": True,
        "allowed": [],
        "blocked": [],
    },
    "git": {
        "auto_commit": False,
        "auto_push": False,
    },
    "ui": {
        "show_welcome": True,
        "show_status": True,
        "show_tools": True,
    },
    "hooks": {
        "enabled": False,
        "on_start": [],
        "on_tool": [],
        "on_message": [],
    },
}


@dataclass
class Config:
    """Configuration class"""
    model: str = "qwen2.5-coder"
    backend: str = "opencode"
    api_key: str = ""
    color: bool = True
    stream: bool = True
    auto_save: bool = True
    vim_mode: bool = False
    theme: str = "default"
    font_size: int = 14
    max_tokens: int = 4096
    temperature: float = 0.7
    tools_enabled: bool = True
    git_auto_commit: bool = False
    git_auto_push: bool = False
    show_welcome: bool = True
    show_status: bool = True
    show_tools: bool = True
    hooks_enabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "backend": self.backend,
            "api_key": self.api_key,
            "color": self.color,
            "stream": self.stream,
            "auto_save": self.auto_save,
            "vim_mode": self.vim_mode,
            "theme": self.theme,
            "font_size": self.font_size,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "tools": {
                "enabled": self.tools_enabled,
                "allowed": [],
                "blocked": [],
            },
            "git": {
                "auto_commit": self.git_auto_commit,
                "auto_push": self.git_auto_push,
            },
            "ui": {
                "show_welcome": self.show_welcome,
                "show_status": self.show_status,
                "show_tools": self.show_tools,
            },
            "hooks": {
                "enabled": self.hooks_enabled,
                "on_start": [],
                "on_tool": [],
                "on_message": [],
            },
        }


class ConfigManager:
    """Configuration manager with file persistence"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            home = os.path.expanduser("~")
            config_path = os.path.join(home, ".galaxy_destroyer", "config.json")
        
        self.config_path = config_path
        self._config: Config = Config()
        self._load()
    
    def _load(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                for key, value in data.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
            except Exception:
                pass
    
    def _save(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self._config.to_dict(), f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self._save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.to_dict()
    
    def reset(self):
        """Reset to default configuration"""
        self._config = Config()
        self._save()


_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str = None, _context: Any = None) -> Any:
    """Get configuration value(s)"""
    manager = get_config_manager()
    if key is None:
        return manager.get_all()
    return manager.get(key)


def set_config(key: str, value: Any, _context: Any = None) -> Dict:
    """Set a configuration value"""
    manager = get_config_manager()
    manager.set(key, value)
    return {"key": key, "value": value, "saved": True}


def config_get(key: str = None, _context: Any = None) -> Any:
    """Get config value (alias)"""
    return get_config(key)


def config_set(key: str, value: Any, _context: Any = None) -> Dict:
    """Set config value (alias)"""
    return set_config(key, value)