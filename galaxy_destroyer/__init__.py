"""Galaxy Destroyer - Terminal AI Assistant"""

__version__ = "0.1.0"
__author__ = "Galaxy Team"
__license__ = "MIT"

from galaxy_destroyer.core.app import GalaxyApp
from galaxy_destroyer.core.state import Context, State
from galaxy_destroyer.commands import register_command, get_commands, execute_command
from galaxy_destroyer.services.tools import get_executor
from galaxy_destroyer.tools.registry import register_tool, tool_registry
from galaxy_destroyer.services.api import create_client

__all__ = [
    "GalaxyApp",
    "Context",
    "State",
    "register_command",
    "get_commands",
    "execute_command",
    "get_executor",
    "register_tool",
    "create_client",
    "__version__",
]
