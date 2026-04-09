"""MCP tools for Galaxy Destroyer"""

import asyncio
from typing import Any, Dict

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter
from galaxy_destroyer.services.mcp import (
    list_mcp_tools,
    list_mcp_resources,
    call_mcp_tool,
)


@register_tool(
    name="mcp_list_tools",
    description="List available MCP tools",
    category=ToolCategory.SYSTEM,
)
def mcp_list_tools(_context: Any = None) -> Dict:
    tools = list_mcp_tools()
    return {
        "tools": tools,
        "count": len(tools),
    }


@register_tool(
    name="mcp_list_resources",
    description="List available MCP resources",
    category=ToolCategory.SYSTEM,
)
def mcp_list_resources(_context: Any = None) -> Dict:
    resources = list_mcp_resources()
    return {
        "resources": resources,
        "count": len(resources),
    }


@register_tool(
    name="mcp_call_tool",
    description="Call an MCP tool",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(name="name", description="Tool name", required=True),
        ToolParameter(name="arguments", description="Tool arguments", default={}),
    ],
)
def mcp_call_tool(name: str, arguments: Dict = None, _context: Any = None) -> Dict:
    if arguments is None:
        arguments = {}

    try:
        result = asyncio.run(call_mcp_tool(name, arguments))
        return result
    except Exception as e:
        return {"error": str(e)}
