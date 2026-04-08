"""CLI - Command line interface for Galaxy Destroyer"""

import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import argparse
import asyncio
from typing import Optional

from core.app import GalaxyApp
from core.state import Context, State
from commands import get_commands, execute_command
from services.api import create_client

import commands.builtin
import commands.git
import services.tools.builtin


def print_banner():
    banner = """
    ███████╗██████╗  ██████╗ ███████╗ ██████╗     ███████╗ █████╗  ██████╗██╗  ██╗
    ██╔════╝██╔══██╗██╔═══██╗██╔════╝██╔═══██╗    ██╔════╝██╔══██╗██╔════╝██║  ██║
    ███████╗██████╔╝██║   ██║█████╗  ██████╔╝    █████╗  ███████║██║     ███████║
    ╚════██║██╔═══╝ ██║   ██║██╔══╝  ██╔══██╗    ██╔══╝  ██╔══██║██║     ██╔══██║
    ███████║██║     ╚██████╔╝███████╗██║  ██║    ██║     ██║  ██║╚██████╗██║  ██║
    ╚══════╝╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
    
                    ╔═══════════════════════════════════╗
                    ║   Galaxy Destroyer v0.1.0         ║
                    ║   AI-Powered Terminal Assistant   ║
                    ╚═══════════════════════════════════╝
    """
    print(banner)


class GalaxyCLI(GalaxyApp):
    """Full-featured CLI with AI integration"""
    
    def __init__(self, model: str = "claude-opus-4-5-20251114"):
        super().__init__()
        self._setup_handlers()
        self._load_tools()
        self.context.model = model
    
    def _setup_handlers(self):
        self.on("command", self._handle_command)
        self.on("complete", self._handle_completion)
    
    def _load_tools(self):
        from services.tools import get_executor
        self._tool_executor = get_executor()
    
    def _handle_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return
        
        cmd_name = parts[0]
        args = parts[1:]
        
        if cmd_name in ("ai", "ask", "chat"):
            self._handle_ai(args)
            return
        
        if cmd_name == "tool":
            self._handle_tool(args)
            return
        
        if cmd_name == "tools":
            self._list_tools()
            return
        
        if cmd_name.startswith("/"):
            cmd_name = cmd_name[1:]
        
        result = execute_command(cmd_name, args, app=self)
        if result:
            self.add_output(result)
        else:
            self.mark_dirty()
    
    def _handle_ai(self, args):
        if not args:
            self.add_output("Usage: ask <question>")
            return
        
        question = " ".join(args)
        self.add_output(f"[AI] Thinking about: {question}...")
        
        if not self.context.auth_token:
            self.add_output("[AI] No API key configured. Set ANTHROPIC_API_KEY")
            return
        
        asyncio.create_task(self._call_ai(question))
    
    async def _call_ai(self, question: str):
        try:
            from services.api import create_client
            from services.tools import get_executor
            
            client = create_client(self.context.auth_token)
            executor = get_executor()
            tools_schema = executor.get_tools_schema()
            
            async def on_tool(tool_use):
                result = await self._tool_executor.execute_tool(
                    name=tool_use.name,
                    tool_use_id=tool_use.id,
                    input_data=tool_use.input,
                    context=self.context
                )
                return result
            
            response = await client.send_message(
                system_prompt="You are Galaxy Destroyer, a helpful AI assistant.",
                tools=tools_schema,
                on_tool_use=on_tool
            )
            
            self.context.add_message("user", question)
            self.context.add_message("assistant", response.message.content)
            self.add_output(f"[AI] {response.message.content}")
            
        except Exception as e:
            self.add_output(f"[Error] {str(e)}")
        
        finally:
            self.show_loading(False)
            self.mark_dirty()
    
    def _handle_tool(self, args):
        if not args:
            self.add_output("Usage: tool <name> [args...]")
            return
        
        tool_name = args[0]
        tool_args = args[1:]
        
        input_dict = {}
        for arg in tool_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                input_dict[key] = value
        
        result = asyncio.run(
            self._tool_executor.execute_tool(
                name=tool_name,
                tool_use_id="cli",
                input_data=input_dict,
                context=self.context
            )
        )
        
        if result.status.value == "success":
            self.add_output(f"[Tool] {result.content}")
        else:
            self.add_output(f"[Tool Error] {result.error}")
    
    def _list_tools(self):
        tools = self._tool_executor.list_tools()
        self.add_output(f"Available tools ({len(tools)}):")
        for tool in sorted(tools):
            self.add_output(f"  - {tool}")
    
    def _handle_completion(self, partial: str):
        registry = get_commands()
        
        if partial.startswith('/'):
            partial = partial[1:]
        
        cmds = registry.search(partial)
        if cmds:
            suggestions = ", ".join(c.name for c in cmds[:8])
            self.add_output(f"Suggestions: {suggestions}")
    
    def show_welcome(self):
        welcome = [
            "Welcome to Galaxy Destroyer!",
            "",
            "Commands:",
            "  help          - Show help",
            "  ask <prompt>  - Ask AI a question",
            "  tool <name>   - Run a tool directly",
            "  tools         - List all tools",
            "  status        - Show status",
            "  git           - Git commands",
            "",
            "Tip: Set ANTHROPIC_API_KEY to use AI features",
            ""
        ]
        for line in welcome:
            self.add_output(line)


def interactive_mode(model: str = "claude-opus-4-5-20251114"):
    """Run in interactive TUI mode - beautiful Claude Code-like UI"""
    from tui import BeautifulTUI
    tui = BeautifulTUI()
    tui.run()


def quick_ask(prompt: str, model: str = "claude-opus-4-5-20251114"):
    """Quick ask mode - single query"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        return
    
    async def ask():
        from services.api import create_client
        from services.tools import get_executor
        
        client = create_client(api_key)
        executor = get_executor()
        tools_schema = executor.get_tools_schema()
        
        print(f"\nAsking: {prompt}\n")
        
        response = await client.send_message(
            system_prompt="You are Galaxy Destroyer, a helpful AI assistant.",
            tools=tools_schema,
        )
        
        print(response.message.content)
    
    asyncio.run(ask())


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog="galaxy",
        description="Galaxy Destroyer - AI-powered terminal assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  galaxy                    Start interactive mode
  galaxy ask "hello"       Ask AI a quick question
  galaxy run "ls -la"      Run a shell command
  galaxy tool read_file path=README.md
  
Environment:
  ANTHROPIC_API_KEY    Your Anthropic API key for AI features
        """
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="Command to run (ask, run, tool)"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the command"
    )
    
    parser.add_argument(
        "-m", "--model",
        default="claude-opus-4-5-20251114",
        help="AI model to use (default: claude-opus-4-5-20251114)"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show version"
    )
    
    parser.add_argument(
        "--api-key",
        help="Set API key"
    )
    
    args = parser.parse_args()
    
    if args.version:
        print("Galaxy Destroyer v0.1.0")
        return
    
    if args.api_key:
        os.environ["ANTHROPIC_API_KEY"] = args.api_key
    
    if args.command == "ask" and args.args:
        quick_ask(" ".join(args.args), args.model)
    
    elif args.command == "run" and args.args:
        from services.tools import get_executor
        executor = get_executor()
        result = asyncio.run(executor.execute_tool(
            name="run_shell",
            tool_use_id="cli",
            input_data={"command": " ".join(args.args)},
            context=None
        ))
        print(result.content or result.error)
    
    elif args.command == "tool" and args.args:
        from services.tools import get_executor
        executor = get_executor()
        tool_name = args.args[0]
        tool_args = args.args[1:]
        
        input_dict = {}
        for arg in tool_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                input_dict[key] = value
        
        result = asyncio.run(executor.execute_tool(
            name=tool_name,
            tool_use_id="cli",
            input_data=input_dict,
            context=None
        ))
        print(result.content or result.error)
    
    elif args.command == "tools":
        from services.tools import get_executor
        executor = get_executor()
        tools = sorted(executor.list_tools())
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool}")
    
    else:
        interactive_mode(args.model)


if __name__ == "__main__":
    main()