"""Command system - registers and executes commands"""

from typing import Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


class CommandCategory(Enum):
    GENERAL = "general"
    FILE = "file"
    EDIT = "edit"
    GIT = "git"
    SEARCH = "search"
    SYSTEM = "system"
    HELP = "help"


@dataclass
class Command:
    """Represents a command"""
    name: str
    description: str
    category: CommandCategory = CommandCategory.GENERAL
    aliases: list[str] = None
    usage: str = ""
    examples: list[str] = None
    fn: Callable = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.examples is None:
            self.examples = []


class CommandRegistry:
    """Registry for all commands"""
    
    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._aliases: dict[str, str] = {}
        self._categories: dict[CommandCategory, list[str]] = {
            cat: [] for cat in CommandCategory
        }
    
    def register(self, cmd: Command):
        """Register a command"""
        self._commands[cmd.name] = cmd
        self._categories[cmd.category].append(cmd.name)
        
        for alias in cmd.aliases:
            self._aliases[alias] = cmd.name
    
    def get(self, name: str) -> Optional[Command]:
        """Get command by name or alias"""
        if name in self._commands:
            return self._commands[name]
        if name in self._aliases:
            return self._commands[self._aliases[name]]
        return None
    
    def list_all(self) -> list[Command]:
        """List all commands"""
        return list(self._commands.values())
    
    def list_by_category(self, category: CommandCategory) -> list[Command]:
        """List commands in a category"""
        names = self._categories[category]
        return [self._commands[name] for name in names]
    
    def search(self, query: str) -> list[Command]:
        """Search commands by name or description"""
        query = query.lower()
        results = []
        for cmd in self._commands.values():
            if query in cmd.name.lower() or query in cmd.description.lower():
                results.append(cmd)
        return results


registry = CommandRegistry()


def register_command(
    name: str,
    description: str,
    category: CommandCategory = CommandCategory.GENERAL,
    aliases: list[str] = None,
    usage: str = "",
    examples: list[str] = None
):
    """Decorator to register a command"""
    def decorator(fn: Callable):
        cmd = Command(
            name=name,
            description=description,
            category=category,
            aliases=aliases or [],
            usage=usage,
            examples=examples or [],
            fn=fn
        )
        registry.register(cmd)
        return fn
    return decorator


def get_commands() -> CommandRegistry:
    """Get the command registry"""
    return registry


def execute_command(name: str, args: list[str] = None, app = None) -> Any:
    """Execute a command by name"""
    cmd = registry.get(name)
    if not cmd or not cmd.fn:
        return f"Unknown command: {name}"
    
    try:
        if args is None:
            args = []
        return cmd.fn(*args, app=app)
    except Exception as e:
        return f"Error: {e}"