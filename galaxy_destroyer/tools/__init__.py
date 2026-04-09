"""Tools package - all built-in tools"""

from .registry import (
    ToolCategory,
    ToolParameter,
    Tool,
    ToolRegistry,
    tool_registry,
    register_tool,
    get_tools,
    execute_tool,
    list_tools_json,
)

__all__ = [
    "ToolCategory",
    "ToolParameter",
    "Tool",
    "ToolRegistry",
    "tool_registry",
    "register_tool",
    "get_tools",
    "execute_tool",
    "list_tools_json",
]


def load_all_tools():
    """Load all tool modules to register their tools"""
    import galaxy_destroyer.tools.builtin
    import galaxy_destroyer.tools.task_tools
    import galaxy_destroyer.tools.web_tools
    import galaxy_destroyer.tools.agent_tools
    import galaxy_destroyer.tools.plan_tools
    import galaxy_destroyer.tools.session_tools
    import galaxy_destroyer.tools.skill_tools
    import galaxy_destroyer.tools.mcp_tools
