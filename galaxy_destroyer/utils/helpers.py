"""Utility functions package"""

import os
import sys
import json
import hashlib
import re
from typing import Any, Optional, Dict, List, Callable
from pathlib import Path
from datetime import datetime
import subprocess


def get_cwd() -> str:
    """Get current working directory"""
    return os.getcwd()


def set_cwd(path: str) -> None:
    """Set current working directory"""
    os.chdir(path)


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in path"""
    return os.path.expandvars(os.path.expanduser(path))


def file_exists(path: str) -> bool:
    """Check if file exists"""
    return os.path.exists(path)


def is_file(path: str) -> bool:
    """Check if path is a file"""
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    """Check if path is a directory"""
    return os.path.isdir(path)


def get_env(key: str, default: str = "") -> str:
    """Get environment variable"""
    return os.environ.get(key, default)


def set_env(key: str, value: str) -> None:
    """Set environment variable"""
    os.environ[key] = value


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string"""
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")


def read_json(path: str) -> Dict:
    """Read JSON file"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def write_json(path: str, data: Any, indent: int = 2) -> bool:
    """Write JSON file"""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        return False


def parse_args(args: str) -> List[str]:
    """Parse command line arguments (respecting quotes)"""
    import shlex
    return shlex.split(args)


def timestamp() -> str:
    """Get current timestamp"""
    return datetime.now().isoformat()


def format_size(bytes: int) -> str:
    """Format byte size to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}PB"


def truncate(text: str, length: int, suffix: str = "...") -> str:
    """Truncate text to length"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def get_platform() -> str:
    """Get platform (linux, darwin, windows)"""
    return sys.platform


def is_linux() -> bool:
    """Check if running on Linux"""
    return sys.platform.startswith('linux')


def is_macos() -> bool:
    """Check if running on macOS"""
    return sys.platform == 'darwin'


def is_windows() -> bool:
    """Check if running on Windows"""
    return sys.platform == 'win32'


def run_command(cmd: str, cwd: Optional[str] = None, timeout: float = 30) -> Dict:
    """Run shell command and return result"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout", "returncode": -1}
    except Exception as e:
        return {"error": str(e), "returncode": -1}


def ensure_dir(path: str) -> bool:
    """Ensure directory exists"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def read_lines(path: str, limit: int = 1000) -> List[str]:
    """Read file lines"""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return [line.rstrip('\n') for line in f][:limit]
    except Exception:
        return []


def write_lines(path: str, lines: List[str]) -> bool:
    """Write lines to file"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return True
    except Exception:
        return False


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_get(d: Dict, key: str, default: Any = None) -> Any:
    """Get nested dict value using dot notation"""
    keys = key.split('.')
    value = d
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            return default
        if value is None:
            return default
    return value


def deep_set(d: Dict, key: str, value: Any) -> None:
    """Set nested dict value using dot notation"""
    keys = key.split('.')
    current = d
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value


class ConfigManager:
    """Simple config file manager"""
    
    def __init__(self, path: str = "~/.galaxy_destroyer_config.json"):
        self.path = os.path.expanduser(path)
        self._data = {}
        self.load()
    
    def load(self) -> None:
        """Load config from file"""
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r') as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
    
    def save(self) -> None:
        """Save config to file"""
        try:
            ensure_dir(os.path.dirname(self.path))
            with open(self.path, 'w') as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set config value"""
        self._data[key] = value
        self.save()
    
    def delete(self, key: str) -> None:
        """Delete config key"""
        if key in self._data:
            del self._data[key]
            self.save()
    
    def all(self) -> Dict:
        """Get all config"""
        return self._data.copy()


class LogManager:
    """Simple logging"""
    
    def __init__(self, name: str = "galaxy_destroyer"):
        self.name = name
        self.level = "INFO"
    
    def _log(self, level: str, message: str):
        print(f"[{timestamp()}] [{level}] {self.name}: {message}")
    
    def debug(self, message: str):
        if self.level == "DEBUG":
            self._log("DEBUG", message)
    
    def info(self, message: str):
        self._log("INFO", message)
    
    def warning(self, message: str):
        self._log("WARNING", message)
    
    def error(self, message: str):
        self._log("ERROR", message)
    
    def critical(self, message: str):
        self._log("CRITICAL", message)


logger = LogManager()