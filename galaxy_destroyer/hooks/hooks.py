"""Hooks system - event hooks for extensibility"""

import os
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class HookEvent(Enum):
    """Available hook events"""
    ON_START = "on_start"
    ON_MESSAGE = "on_message"
    ON_TOOL_START = "on_tool_start"
    ON_TOOL_END = "on_tool_end"
    ON_ERROR = "on_error"
    ON_EXIT = "on_exit"
    ON_SESSION_START = "on_session_start"
    ON_SESSION_END = "on_session_end"


@dataclass
class Hook:
    """A hook definition"""
    event: HookEvent
    name: str
    script: str
    enabled: bool = True
    description: str = ""


class HookManager:
    """Manages hooks"""
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[Hook]] = {
            event: [] for event in HookEvent
        }
        self._load_hooks()
    
    def _load_hooks(self):
        """Load hooks from config directory"""
        hooks_dir = self._get_hooks_dir()
        
        if not os.path.isdir(hooks_dir):
            return
        
        for filename in os.listdir(hooks_dir):
            if filename.endswith(('.sh', '.py', '.js')):
                self._load_hook_file(os.path.join(hooks_dir, filename))
    
    def _get_hooks_dir(self) -> str:
        """Get hooks directory"""
        return os.path.join(os.path.expanduser("~"), ".galaxy_destroyer", "hooks")
    
    def _load_hook_file(self, filepath: str):
        """Load a hook from file"""
        name = os.path.splitext(os.path.basename(filepath))[0]
        
        for event in HookEvent:
            if event.value in name:
                hook = Hook(
                    event=event,
                    name=name,
                    script=filepath,
                    description=f"Loaded from {filepath}",
                )
                self._hooks[event].append(hook)
                break
    
    def register_hook(self, event: HookEvent, hook: Hook):
        """Register a hook"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)
    
    def get_hooks(self, event: HookEvent) -> List[Hook]:
        """Get hooks for an event"""
        return [h for h in self._hooks.get(event, []) if h.enabled]
    
    def enable_hook(self, name: str) -> bool:
        """Enable a hook by name"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    hook.enabled = True
                    return True
        return False
    
    def disable_hook(self, name: str) -> bool:
        """Disable a hook by name"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    hook.enabled = False
                    return True
        return False
    
    def list_hooks(self) -> List[Dict]:
        """List all hooks"""
        result = []
        for event, hooks in self._hooks.items():
            for hook in hooks:
                result.append({
                    "name": hook.name,
                    "event": event.value,
                    "enabled": hook.enabled,
                    "script": hook.script,
                    "description": hook.description,
                })
        return result


_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """Get global hook manager"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


async def trigger_hook(event: HookEvent, context: Dict[str, Any] = None):
    """Trigger hooks for an event"""
    hooks = get_hook_manager().get_hooks(event)
    
    for hook in hooks:
        try:
            await run_hook_script(hook.script, event.value, context or {})
        except Exception as e:
            print(f"Hook error: {hook.name}: {e}")


async def run_hook_script(script: str, event: str, context: Dict) -> bool:
    """Run a hook script"""
    import subprocess
    
    try:
        env = os.environ.copy()
        for key, value in context.items():
            env[f"GALAXY_{key.upper()}"] = str(value)
        
        result = subprocess.run(
            [script],
            env=env,
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except:
        return False


def on_start():
    """Trigger on start hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(HookEvent.ON_START))


def on_message(message: str):
    """Trigger on message hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(HookEvent.ON_MESSAGE, {"message": message}))


def on_tool_start(tool_name: str, tool_input: Dict):
    """Trigger on tool start hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(
        HookEvent.ON_TOOL_START, 
        {"tool": tool_name, "input": tool_input}
    ))


def on_tool_end(tool_name: str, result: Any):
    """Trigger on tool end hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(
        HookEvent.ON_TOOL_END,
        {"tool": tool_name, "result": str(result)}
    ))


def on_error(error: Exception):
    """Trigger on error hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(
        HookEvent.ON_ERROR,
        {"error": str(error), "type": type(error).__name__}
    ))


def on_exit():
    """Trigger on exit hooks"""
    import asyncio
    asyncio.create_task(trigger_hook(HookEvent.ON_EXIT))