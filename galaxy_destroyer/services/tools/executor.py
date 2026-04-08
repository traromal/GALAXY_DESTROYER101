"""Tool execution service - orchestrates tool calls"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ToolResultStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    tool_use_id: str
    tool_name: str
    status: ToolResultStatus
    content: str
    error: Optional[str] = None
    execution_time: float = 0.0


class ToolExecutor:
    """Executes tools and manages tool lifecycle"""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tool_schemas: Dict[str, Dict] = {}
        self._hooks = {
            "before_execute": [],
            "after_execute": [],
            "on_error": [],
        }
        self._running_tools: Dict[str, asyncio.Task] = {}
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        parameters: Dict[str, Any] = None
    ):
        """Register a tool with its handler"""
        self._tools[name] = handler
        self._tool_schemas[name] = {
            "name": name,
            "description": description,
            "parameters": parameters or {"type": "object", "properties": {}}
        }
    
    def get_tools_schema(self) -> List[Dict]:
        """Get all tools as Anthropic-compatible schema"""
        return list(self._tool_schemas.values())
    
    def get_tool_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler by name"""
        return self._tools.get(name)
    
    def add_before_hook(self, callback: Callable):
        """Add before-execution hook"""
        self._hooks["before_execute"].append(callback)
    
    def add_after_hook(self, callback: Callable):
        """Add after-execution hook"""
        self._hooks["after_execute"].append(callback)
    
    def add_error_hook(self, callback: Callable):
        """Add error hook"""
        self._hooks["on_error"].append(callback)
    
    async def execute_tool(
        self,
        name: str,
        tool_use_id: str,
        input_data: Dict[str, Any],
        context: Optional[Any] = None,
        timeout: float = 60.0
    ) -> ToolResult:
        """Execute a single tool"""
        import time
        start_time = time.time()
        
        for hook in self._hooks["before_execute"]:
            try:
                hook(name, input_data, context)
            except Exception as e:
                pass
        
        if name not in self._tools:
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=name,
                status=ToolResultStatus.ERROR,
                content="",
                error=f"Unknown tool: {name}",
                execution_time=time.time() - start_time
            )
        
        handler = self._tools[name]
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(**input_data, _context=context),
                    timeout=timeout
                )
            else:
                result = handler(**input_data, _context=context)
            
            result_content = self._format_result(result)
            
            for hook in self._hooks["after_execute"]:
                try:
                    hook(name, input_data, result, context)
                except Exception as e:
                    pass
            
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=name,
                status=ToolResultStatus.SUCCESS,
                content=result_content,
                execution_time=time.time() - start_time
            )
            
        except asyncio.TimeoutError:
            for hook in self._hooks["on_error"]:
                try:
                    hook(name, input_data, "Timeout", context)
                except Exception as e:
                    pass
            
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=name,
                status=ToolResultStatus.TIMEOUT,
                content="",
                error=f"Tool execution timed out after {timeout}s",
                execution_time=timeout
            )
            
        except Exception as e:
            error_msg = str(e)
            
            for hook in self._hooks["on_error"]:
                try:
                    hook(name, input_data, error_msg, context)
                except Exception as hook_error:
                    pass
            
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=name,
                status=ToolResultStatus.ERROR,
                content="",
                error=error_msg,
                execution_time=time.time() - start_time
            )
    
    async def execute_tools(
        self,
        tool_uses: List[Dict],
        context: Optional[Any] = None,
        parallel: bool = True
    ) -> List[ToolResult]:
        """Execute multiple tools"""
        if parallel:
            tasks = [
                self.execute_tool(
                    name=t["name"],
                    tool_use_id=t["id"],
                    input_data=t["input"],
                    context=context
                )
                for t in tool_uses
            ]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for t in tool_uses:
                result = await self.execute_tool(
                    name=t["name"],
                    tool_use_id=t["id"],
                    input_data=t["input"],
                    context=context
                )
                results.append(result)
            return results
    
    def _format_result(self, result: Any) -> str:
        """Format tool result for API"""
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            return json.dumps(result, indent=2)
        if isinstance(result, list):
            return json.dumps(result, indent=2)
        return str(result)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self._tools.keys())


_executor = ToolExecutor()


def get_executor() -> ToolExecutor:
    """Get the global tool executor"""
    return _executor


def register_tool(
    name: str,
    description: str = "",
    parameters: Dict[str, Any] = None
):
    """Decorator to register a tool"""
    def decorator(fn: Callable):
        _executor.register_tool(name, fn, description, parameters)
        return fn
    return decorator