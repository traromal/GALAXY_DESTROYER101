"""Tools package - tool execution system"""

from .executor import ToolExecutor, ToolResult, ToolResultStatus, get_executor


def _load_all_tools():
    """Load all built-in tools"""
    from tools.registry import tool_registry

    try:
        import tools.builtin
    except ImportError:
        pass

    try:
        import tools.task_tools
    except ImportError:
        pass

    try:
        import tools.web_tools
    except ImportError:
        pass

    try:
        import tools.agent_tools
    except ImportError:
        pass

    try:
        import tools.plan_tools
    except ImportError:
        pass

    try:
        import tools.session_tools
    except ImportError:
        pass

    return tool_registry


def get_executor() -> ToolExecutor:
    """Get or create the tool executor with all tools loaded"""
    from .executor import _executor

    if _executor is None:
        _load_all_tools()
    return _executor


__all__ = [
    "ToolExecutor",
    "ToolResult",
    "ToolResultStatus",
    "get_executor",
    "get_executor",
]
