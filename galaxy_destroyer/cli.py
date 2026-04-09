"""CLI - Command line interface for Galaxy Destroyer"""

import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import argparse
import asyncio
from typing import Optional

from galaxy_destroyer.core.app import GalaxyApp
from galaxy_destroyer.core.state import Context, State
from galaxy_destroyer.core.bootstrap import (
    build_full_system_prompt,
    format_welcome_message,
    format_status,
    SessionInfo,
)
from galaxy_destroyer.commands import get_commands, execute_command
from galaxy_destroyer.services.api import Backend, create_client

import galaxy_destroyer.commands.builtin
import galaxy_destroyer.commands.git
import galaxy_destroyer.services.tools.builtin


def print_banner():
    print("Galaxy Destroyer v0.1.0 - AI-Powered Terminal Assistant")
    print("")


class GalaxyCLI(GalaxyApp):
    """Full-featured CLI with AI integration"""

    def __init__(self, model: str = "qwen2.5-coder", backend: str = "opencode"):
        super().__init__()
        self._setup_handlers()
        self._load_tools()
        self._load_config()
        self.context.model = model
        self.context.backend = backend
        self.session = SessionInfo.create()
        self._system_prompt = None

    def _setup_handlers(self):
        self.on("command", self._handle_command)
        self.on("complete", self._handle_completion)

    def _load_tools(self):
        from galaxy_destroyer.services.tools import get_executor

        self._tool_executor = get_executor()

    def _load_config(self):
        from galaxy_destroyer.services.config import get_config

        config = get_config()
        if config.get("vim_mode"):
            self.context.vim_mode = True

    def get_system_prompt(self) -> str:
        """Get the system prompt for AI"""
        if self._system_prompt is None:
            self._system_prompt = build_full_system_prompt(
                model=self.context.model,
                backend=self.context.backend,
            )
        return self._system_prompt

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

        if cmd_name == "agents":
            self._list_agents()
            return

        if cmd_name == "backend":
            self._handle_backend(args)
            return

        if cmd_name == "model":
            self._handle_model(args)
            return

        if cmd_name in ("status", "session"):
            self._show_status()
            return

        if cmd_name in ("help", "?"):
            self._show_help()
            return

        if cmd_name in ("clear", "reset"):
            self._clear_session()
            return

        if cmd_name.startswith("/"):
            cmd_name = cmd_name[1:]

        result = execute_command(cmd_name, args, app=self)
        if result:
            self.add_output(result)
        else:
            self.mark_dirty()

    def _handle_model(self, args):
        if not args:
            self.add_output(f"Current model: {self.context.model}")
            self.add_output(
                "Available: qwen2.5-coder, llama3, gpt-4, claude-opus-4-5-20251114"
            )
            return

        model = args[0]
        self.context.model = model
        self._system_prompt = None
        self.add_output(f"Model set to: {model}")

    def _show_status(self):
        status = format_status(self.context.model, self.context.backend, self.session)
        self.add_output(status)

    def _show_help(self):
        help_text = """
=== Galaxy Destroyer Commands ===

AI Commands:
  ask <prompt>     - Ask AI a question
  chat             - Start conversation mode
  agents           - List available agents

Tool Commands:
  tool <name>      - Run a tool directly
  tools            - List all available tools

Configuration:
  backend <name>   - Set backend (opencode, ollama, openai, anthropic)
  model <name>     - Set model
  config           - Show configuration

Session:
  status           - Show current status
  clear            - Clear conversation history

Git Commands:
  git status       - Show git status
  git log          - Show commit history
  git diff         - Show changes
  git commit       - Commit changes

Task Commands:
  task create      - Create a task
  task list        - List tasks
  task update      - Update task

Other:
  help             - Show this help
  exit             - Exit Galaxy Destroyer
"""
        self.add_output(help_text)

    def _clear_session(self):
        self._message_history = []
        self._system_prompt = None
        self.add_output("Conversation cleared!")

    def _handle_backend(self, args):
        if not args:
            backends = ["opencode", "ollama", "openai", "anthropic"]
            self.add_output(f"Available backends: {', '.join(backends)}")
            self.add_output(f"Current: {self.context.backend}")
            return

        backend_name = args[0].lower()
        if backend_name in ["opencode", "ollama", "openai", "anthropic"]:
            self.context.backend = backend_name
            self._system_prompt = None
            self.add_output(f"Backend set to: {backend_name}")
        else:
            self.add_output(f"Unknown backend: {backend_name}")

    def _handle_ai(self, args):
        if not args:
            self.add_output("Usage: ask <question>")
            return

        question = " ".join(args)
        self.add_output(f"[AI] Thinking about: {question}...")

        if not self.context.backend:
            self.add_output("[AI] No backend configured. Use: backend opencode")
            return

        asyncio.create_task(self._call_ai(question))

    async def _call_ai(self, question: str):
        try:
            from galaxy_destroyer.services.api import create_client, Backend

            backend_map = {
                "opencode": Backend.OPENCODE,
                "ollama": Backend.OLLAMA,
                "openai": Backend.OPENAI,
                "anthropic": Backend.ANTHROPIC,
            }

            backend = backend_map.get(self.context.backend, Backend.OPENCODE)
            api_key = os.environ.get(f"{self.context.backend.upper()}_API_KEY", "")

            client = create_client(api_key, backend=backend, model=self.context.model)
            executor = get_executor()
            tools_schema = executor.get_tools_schema()

            async def on_tool(tool_use):
                result = await self._tool_executor.execute_tool(
                    name=tool_use.name,
                    tool_use_id=tool_use.id,
                    input_data=tool_use.input,
                    context=self.context,
                )
                return result

            system_prompt = self.get_system_prompt()

            response = await client.send_message(
                system_prompt=system_prompt, tools=tools_schema, on_tool_use=on_tool
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
            if "=" in arg:
                key, value = arg.split("=", 1)
                input_dict[key] = value

        result = asyncio.run(
            self._tool_executor.execute_tool(
                name=tool_name,
                tool_use_id="cli",
                input_data=input_dict,
                context=self.context,
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

    def _list_agents(self):
        from galaxy_destroyer.services.agents import list_agents

        agents = list_agents()
        self.add_output("Available agents:")
        for name, desc in agents.items():
            self.add_output(f"  {name}: {desc}")

    def _handle_completion(self, partial: str):
        registry = get_commands()

        if partial.startswith("/"):
            partial = partial[1:]

        cmds = registry.search(partial)
        if cmds:
            suggestions = ", ".join(c.name for c in cmds[:8])
            self.add_output(f"Suggestions: {suggestions}")

    def show_welcome(self):
        welcome = format_welcome_message(self.context.model, self.context.backend)
        for line in welcome.split("\n"):
            self.add_output(line)


def interactive_mode(model: str = "qwen2.5-coder", backend: str = "opencode"):
    """Run in interactive TUI mode - beautiful Claude Code-like UI"""
    from galaxy_destroyer.tui import BeautifulTUI

    tui = BeautifulTUI()
    tui.run()


def quick_ask(prompt: str, model: str = "qwen2.5-coder", backend: str = "opencode"):
    """Quick ask mode - single query"""
    api_key = os.environ.get(f"{backend.upper()}_API_KEY", "")

    async def ask():
        from galaxy_destroyer.services.api import create_client, Backend
        from galaxy_destroyer.services.tools import get_executor

        backend_map = {
            "opencode": Backend.OPENCODE,
            "ollama": Backend.OLLAMA,
            "openai": Backend.OPENAI,
            "anthropic": Backend.ANTHROPIC,
        }

        system_prompt = build_full_system_prompt(model, backend)

        client = create_client(
            api_key, backend=backend_map.get(backend, Backend.OPENCODE), model=model
        )
        executor = get_executor()
        tools_schema = executor.get_tools_schema()

        print(f"\nAsking: {prompt}\n")

        response = await client.send_message(
            system_prompt=system_prompt,
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
  galaxy -b ollama ask "debug this"
  
Backends:
  opencode   - OpenCode.ai (default, free, no key needed)
  ollama     - Local Ollama
  openai     - OpenAI API
  anthropic  - Anthropic Claude API

Environment:
  OPENCODE_API_KEY    For OpenCode.ai (usually not needed)
  OLLAMA_HOST         For local Ollama (default: localhost:11434)
  OPENAI_API_KEY     For OpenAI
  ANTHROPIC_API_KEY  For Claude
        """,
    )

    parser.add_argument("command", nargs="?", help="Command to run (ask, run, tool)")

    parser.add_argument("args", nargs="*", help="Arguments for the command")

    parser.add_argument(
        "-m", "--model", default="qwen2.5-coder", help="AI model to use"
    )

    parser.add_argument(
        "-b",
        "--backend",
        default="opencode",
        choices=["opencode", "ollama", "openai", "anthropic"],
        help="AI backend to use",
    )

    parser.add_argument("-v", "--version", action="store_true", help="Show version")

    parser.add_argument("--api-key", help="Set API key")

    args = parser.parse_args()

    if args.version:
        print("Galaxy Destroyer v0.1.0")
        return

    if args.api_key:
        os.environ[f"{args.backend.upper()}_API_KEY"] = args.api_key

    if args.command == "ask" and args.args:
        quick_ask(" ".join(args.args), args.model, args.backend)

    elif args.command == "run" and args.args:
        from galaxy_destroyer.services.tools import get_executor

        executor = get_executor()
        result = asyncio.run(
            executor.execute_tool(
                name="run_shell",
                tool_use_id="cli",
                input_data={"command": " ".join(args.args)},
                context=None,
            )
        )
        print(result.content or result.error)

    elif args.command == "tool" and args.args:
        from galaxy_destroyer.services.tools import get_executor

        executor = get_executor()
        tool_name = args.args[0]
        tool_args = args.args[1:]

        input_dict = {}
        for arg in tool_args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                input_dict[key] = value

        result = asyncio.run(
            executor.execute_tool(
                name=tool_name, tool_use_id="cli", input_data=input_dict, context=None
            )
        )
        print(result.content or result.error)

    elif args.command == "tools":
        from galaxy_destroyer.services.tools import get_executor

        executor = get_executor()
        tools = sorted(executor.list_tools())
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool}")

    elif args.command == "agents":
        from galaxy_destroyer.services.agents import list_agents

        agents = list_agents()
        print("Available agents:")
        for name, desc in agents.items():
            print(f"  {name}: {desc}")

    else:
        interactive_mode(args.model, args.backend)


if __name__ == "__main__":
    main()
