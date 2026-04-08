"""Tool execution system - similar to the TypeScript tool system"""

from typing import Callable, Optional, Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum
import json
import inspect


class ToolCategory(Enum):
    FILE = "file"
    EDIT = "edit"
    SEARCH = "search"
    GIT = "git"
    SYSTEM = "system"
    CODE = "code"
    DATA = "data"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    description: str
    type: str = "string"
    required: bool = False
    default: Any = None
    enum: List[str] = None


@dataclass
class Tool:
    """Tool definition"""
    name: str
    description: str
    category: ToolCategory = ToolCategory.SYSTEM
    parameters: List[ToolParameter] = field(default_factory=list)
    fn: Callable = None
    enabled: bool = True
    
    def validate_params(self, params: Dict) -> Optional[str]:
        """Validate parameters"""
        for param in self.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"
            
            if param.name in params:
                value = params[param.name]
                
                if param.enum and value not in param.enum:
                    return f"Invalid value for {param.name}. Must be one of: {', '.join(param.enum)}"
        
        return None


class ToolRegistry:
    """Registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        self._hooks = {
            "before_execute": [],
            "after_execute": [],
            "on_error": [],
        }
    
    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name] = tool
        self._categories[tool.category].append(tool.name)
    
    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def list_all(self) -> List[Tool]:
        """List all tools"""
        return list(self._tools.values())
    
    def list_by_category(self, category: ToolCategory) -> List[Tool]:
        """List tools in a category"""
        names = self._categories[category]
        return [self._tools[name] for name in names]
    
    def enable(self, name: str):
        """Enable a tool"""
        if name in self._tools:
            self._tools[name].enabled = True
    
    def disable(self, name: str):
        """Disable a tool"""
        if name in self._tools:
            self._tools[name].enabled = False
    
    def hook_before(self, callback: Callable):
        """Add before-execute hook"""
        self._hooks["before_execute"].append(callback)
    
    def hook_after(self, callback: Callable):
        """Add after-execute hook"""
        self._hooks["after_execute"].append(callback)
    
    def hook_error(self, callback: Callable):
        """Add error hook"""
        self._hooks["on_error"].append(callback)
    
    def execute(self, name: str, params: Dict = None, context: Any = None) -> Any:
        """Execute a tool"""
        if params is None:
            params = {}
        
        tool = self.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        
        if not tool.enabled:
            return {"error": f"Tool disabled: {name}"}
        
        for hook in self._hooks["before_execute"]:
            hook(name, params, context)
        
        try:
            error = tool.validate_params(params)
            if error:
                raise ValueError(error)
            
            result = tool.fn(**params, _context=context)
            
            for hook in self._hooks["after_execute"]:
                hook(name, params, result, context)
            
            return result
        
        except Exception as e:
            for hook in self._hooks["on_error"]:
                hook(name, params, e, context)
            return {"error": str(e)}


tool_registry = ToolRegistry()


def register_tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.SYSTEM,
    parameters: List[ToolParameter] = None
):
    """Decorator to register a tool"""
    def decorator(fn: Callable):
        tool = Tool(
            name=name,
            description=description,
            category=category,
            parameters=parameters or [],
            fn=fn
        )
        tool_registry.register(tool)
        return fn
    return decorator


def get_tools() -> ToolRegistry:
    """Get the tool registry"""
    return tool_registry


def execute_tool(name: str, params: Dict = None, context: Any = None) -> Any:
    """Execute a tool by name"""
    return tool_registry.execute(name, params, context)


def list_tools_json() -> str:
    """List all tools as JSON"""
    tools = []
    for tool in tool_registry.list_all():
        tools.append({
            "name": tool.name,
            "description": tool.description,
            "category": tool.category.value,
            "enabled": tool.enabled,
            "parameters": [
                {
                    "name": p.name,
                    "description": p.description,
                    "type": p.type,
                    "required": p.required,
                    "enum": p.enum,
                }
                for p in tool.parameters
            ]
        })
    return json.dumps(tools, indent=2)