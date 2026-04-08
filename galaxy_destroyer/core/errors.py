"""Error handling and logging system"""

import traceback
import sys
import os
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ErrorLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Error record for logging"""
    level: ErrorLevel
    message: str
    exception: Optional[str] = None
    traceback: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "galaxy_destroyer"


class ErrorHandler:
    """Central error handling"""
    
    def __init__(self, log_path: Optional[str] = None):
        if log_path is None:
            home = os.path.expanduser("~")
            log_path = os.path.join(home, ".galaxy_destroyer", "errors.log")
        
        self.log_path = log_path
        self._errors: list[ErrorRecord] = []
        self._setup_logging()
    
    def _setup_logging(self):
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
    
    def log(self, level: ErrorLevel, message: str, exception: Optional[Exception] = None, context: Dict = None):
        """Log an error"""
        trace = None
        exc_str = None
        
        if exception:
            exc_str = str(exception)
            trace = traceback.format_exc()
        
        record = ErrorRecord(
            level=level,
            message=message,
            exception=exc_str,
            traceback=trace,
            context=context or {},
        )
        
        self._errors.append(record)
        
        self._write_to_log(record)
        
        if level in (ErrorLevel.ERROR, ErrorLevel.CRITICAL):
            self._print_error(record)
    
    def _write_to_log(self, record: ErrorRecord):
        """Write error to log file"""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps({
                    "timestamp": record.timestamp,
                    "level": record.level.value,
                    "message": record.message,
                    "exception": record.exception,
                    "traceback": record.traceback,
                    "context": record.context,
                }) + "\n")
        except:
            pass
    
    def _print_error(self, record: ErrorRecord):
        """Print error to console"""
        if record.level == ErrorLevel.CRITICAL:
            prefix = "💥 CRITICAL"
        elif record.level == ErrorLevel.ERROR:
            prefix = "❌ ERROR"
        elif record.level == ErrorLevel.WARNING:
            prefix = "⚠️ WARNING"
        else:
            prefix = "ℹ️ INFO"
        
        print(f"{prefix}: {record.message}", file=sys.stderr)
        if record.exception:
            print(f"  Exception: {record.exception}", file=sys.stderr)
    
    def debug(self, message: str, **context):
        self.log(ErrorLevel.DEBUG, message, context=context)
    
    def info(self, message: str, **context):
        self.log(ErrorLevel.INFO, message, context=context)
    
    def warning(self, message: str, **context):
        self.log(ErrorLevel.WARNING, message, context=context)
    
    def error(self, message: str, exception: Exception = None, **context):
        self.log(ErrorLevel.ERROR, message, exception, context)
    
    def critical(self, message: str, exception: Exception = None, **context):
        self.log(ErrorLevel.CRITICAL, message, exception, context)
    
    def get_recent_errors(self, count: int = 10) -> list[ErrorRecord]:
        """Get recent errors"""
        return self._errors[-count:]
    
    def clear_errors(self):
        """Clear error history"""
        self._errors.clear()


_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def log_error(message: str, exception: Exception = None, **context):
    """Convenience function for logging errors"""
    get_error_handler().error(message, exception, **context)


def log_warning(message: str, **context):
    """Convenience function for logging warnings"""
    get_error_handler().warning(message, **context)


def log_info(message: str, **context):
    """Convenience function for logging info"""
    get_error_handler().info(message, **context)


def log_debug(message: str, **context):
    """Convenience function for logging debug"""
    get_error_handler().debug(message, **context)


def format_exception(exc: Exception) -> str:
    """Format exception nicely"""
    return f"{type(exc).__name__}: {str(exc)}"


class GalaxyException(Exception):
    """Base exception for Galaxy Destroyer"""
    
    def __init__(self, message: str, code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp,
        }


class ToolException(GalaxyException):
    """Exception for tool errors"""
    pass


class ApiException(GalaxyException):
    """Exception for API errors"""
    pass


class ConfigException(GalaxyException):
    """Exception for configuration errors"""
    pass


class SessionException(GalaxyException):
    """Exception for session errors"""
    pass


def handle_exception(exc: Exception, context: Dict = None) -> str:
    """Handle exception and return user-friendly message"""
    error_handler = get_error_handler()
    
    if isinstance(exc, GalaxyException):
        error_handler.error(exc.message, exc, context=context)
        return f"Error: {exc.message}"
    
    error_handler.error(str(exc), exc, context=context)
    
    error_type = type(exc).__name__
    return f"An error occurred ({error_type}): {str(exc)}"


def verify_prerequisites() -> Dict[str, Any]:
    """Verify that prerequisites are installed"""
    results = {
        "python": {"installed": False, "version": ""},
        "git": {"installed": False, "version": ""},
        "pip": {"installed": False, "version": ""},
    }
    
    import shutil
    
    results["python"]["installed"] = True
    results["python"]["version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    git_path = shutil.which("git")
    if git_path:
        results["git"]["installed"] = True
        try:
            import subprocess
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            results["git"]["version"] = result.stdout.strip()
        except:
            results["git"]["version"] = "found"
    
    pip_path = shutil.which("pip") or shutil.which("pip3")
    if pip_path:
        results["pip"]["installed"] = True
        results["pip"]["version"] = "found"
    
    return results


def check_environment() -> Dict[str, Any]:
    """Check environment setup"""
    import platform
    
    env = {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "cwd": os.getcwd(),
        "home": os.path.expanduser("~"),
        "prerequisites": verify_prerequisites(),
    }
    
    return env