"""Enhanced TUI - Beautiful Claude Code-like interface"""

import os
import sys
import time
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from core.render import (
    get_terminal_size, clear_screen, move_cursor, write, write_line,
    style, BorderStyle, DOUBLE_BORDER, ROUNDED_BORDER, word_wrap
)
from core.state import Context, State, Color
from core.app import InputHandler, Key


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = 0


class BeautifulTUI:
    """Beautiful Claude Code-like terminal UI"""
    
    def __init__(self):
        self.context = Context()
        self.state = State()
        self.input_handler = InputHandler()
        self.messages: List[ChatMessage] = []
        self.running = False
        self.width = 80
        self.height = 24
        self._needs_render = True
        self._loading = False
        self._loading_text = ""
    
    def run(self):
        """Main run loop"""
        self.running = True
        self.width, self.height = get_terminal_size()
        
        try:
            self._setup()
            self._show_welcome()
            self._main_loop()
        except KeyboardInterrupt:
            self._show_exit()
        finally:
            self._cleanup()
    
    def _setup(self):
        """Setup terminal"""
        if os.name == 'nt':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        self.context.cwd = os.getcwd()
    
    def _show_welcome(self):
        """Show welcome banner"""
        clear_screen()
        
        self._draw_header()
        
        cat_logo = """
      /\\_/\\
     ( o.o )
     (")_(")
"""
        
        welcome_box = [
            style(cat_logo, color="cyan"),
            "",
            style("   ╔═══════════════════════════════════════════╗", color="cyan"),
            style("   ║    Welcome to Galaxy Destroyer v0.1.0    ║", color="cyan", bold=True),
            style("   ║    AI-Powered Terminal Assistant           ║", dim=True),
            style("   ╚═══════════════════════════════════════════╝", color="cyan"),
            "",
            style("   Commands:", bold=True, color="yellow"),
            "     ask <msg>   - Chat with AI",
            "     tool <name> - Run a tool",
            "     run <cmd>   - Execute shell",
            "     help        - Show commands",
            "     clear       - Clear chat",
            "     exit        - Quit",
            "",
            style("   Set ANTHROPIC_API_KEY for AI features", dim=True, color="gray"),
            "",
        ]
        
        for line in welcome_box:
            write_line(line)
        
        self._draw_input_prompt()
        move_cursor(1, self.height)
    
    def _main_loop(self):
        """Main loop"""
        while self.running:
            if self._needs_render:
                self._render()
                self._needs_render = False
            
            key = self.input_handler.read_key()
            
            if key:
                self._handle_key(key)
                self._needs_render = True
            else:
                time.sleep(0.01)
    
    def _handle_key(self, key: Key):
        """Handle key press"""
        if key.name == "ctrl_c" or key.name == "escape":
            self.running = False
            return
        
        if key.name == "enter":
            self._execute_input()
            return
        
        if key.name == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
            return
        
        if key.name == "up":
            self._history_previous()
            return
        
        if key.name == "down":
            self._history_next()
            return
        
        if key.name == "tab":
            return
        
        if len(key.value) == 1 and not key.meta:
            self.state.input_buffer += key.value
    
    def _execute_input(self):
        """Execute input command"""
        cmd = self.state.input_buffer.strip()
        
        if not cmd:
            write_line("")
            self._draw_input_prompt()
            return
        
        self.state.add_to_history(cmd)
        
        self._add_message("user", f"> {cmd}")
        
        if cmd.startswith("ask ") or cmd.startswith("ai ") or cmd.startswith("chat "):
            question = cmd.split(" ", 1)[1] if " " in cmd else ""
            self._handle_ask(question)
        elif cmd == "clear":
            self.messages.clear()
            clear_screen()
            self._draw_header()
        elif cmd == "exit" or cmd == "quit" or cmd == "q":
            self.running = False
        elif cmd.startswith("tool "):
            self._handle_tool(cmd.split(" ", 1)[1])
        elif cmd.startswith("run "):
            self._handle_run(cmd.split(" ", 1)[1])
        elif cmd == "help":
            self._show_help()
        elif cmd == "tools":
            self._list_tools()
        else:
            self._add_message("system", f"Unknown command: {cmd}. Type 'help' for available commands.")
        
        self.state.input_buffer = ""
        
        if self.running:
            self._draw_input_prompt()
    
    def _handle_ask(self, question: str):
        """Handle AI ask"""
        if not question:
            self._add_message("system", "Usage: ask <question>")
            return
        
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self._add_message("system", style("Error: ANTHROPIC_API_KEY not set", color="red"))
            return
        
        self._loading = True
        self._loading_text = f"Thinking about: {question[:50]}..."
        self._needs_render = True
        
        asyncio.run(self._call_ai(question))
        
        self._loading = False
    
    async def _call_ai(self, question: str):
        """Call AI API"""
        try:
            from services.api import create_client
            from services.tools import get_executor
            
            client = create_client(os.environ.get("ANTHROPIC_API_KEY"))
            executor = get_executor()
            tools_schema = executor.get_tools_schema()
            
            response = await client.send_message(
                system_prompt="You are Galaxy Destroyer, a helpful AI assistant.",
                tools=tools_schema,
            )
            
            self._add_message("assistant", response.message.content)
            
        except Exception as e:
            self._add_message("system", style(f"Error: {str(e)}", color="red"))
    
    def _handle_tool(self, args: str):
        """Handle tool command"""
        if not args:
            self._add_message("system", "Usage: tool <name> [args...]")
            return
        
        parts = args.split()
        tool_name = parts[0]
        
        input_dict = {}
        for arg in parts[1:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                input_dict[k] = v
        
        try:
            from services.tools import get_executor
            executor = get_executor()
            result = asyncio.run(executor.execute_tool(
                name=tool_name,
                tool_use_id="cli",
                input_data=input_dict,
                context=self.context
            ))
            
            if result.status.value == "success":
                self._add_message("tool", result.content)
            else:
                self._add_message("system", style(f"Error: {result.error}", color="red"))
        except Exception as e:
            self._add_message("system", style(f"Error: {str(e)}", color="red"))
    
    def _handle_run(self, command: str):
        """Handle run command"""
        if not command:
            self._add_message("system", "Usage: run <command>")
            return
        
        self._handle_tool(f"run_shell command={command}")
    
    def _show_help(self):
        """Show help"""
        help_text = """
╔═══════════════════════════════════════════════════════════╗
║                    AVAILABLE COMMANDS                      ║
╠═══════════════════════════════════════════════════════════╣
║  ask <msg>     - Chat with AI (needs API key)             ║
║  tool <name>  - Run a specific tool                      ║
║  run <cmd>    - Execute shell command                    ║
║  tools        - List all available tools                  ║
║  clear        - Clear the chat                           ║
║  help         - Show this help                            ║
║  exit         - Exit the application                      ║
╠═══════════════════════════════════════════════════════════╣
║                    AVAILABLE TOOLS                         ║
╠═══════════════════════════════════════════════════════════╣
║  read_file, write_file, edit_file, list_directory         ║
║  glob, grep, search_files                                  ║
║  git_status, git_log, git_diff                            ║
║  web_fetch, web_search                                     ║
║  task_create, task_list, task_get, task_update            ║
║  mcp_list_resources, mcp_call_tool                         ║
║  bash, run_shell, repl_eval                                ║
╚═══════════════════════════════════════════════════════════╝
"""
        self._add_message("help", help_text)
    
    def _list_tools(self):
        """List tools"""
        from services.tools import get_executor
        executor = get_executor()
        tools = sorted(executor.list_tools())
        
        tools_text = "Available Tools:\n" + "\n".join(f"  - {t}" for t in tools)
        self._add_message("system", tools_text)
    
    def _add_message(self, role: str, content: str):
        """Add message to chat"""
        self.messages.append(ChatMessage(role=role, content=content, timestamp=time.time()))
    
    def _history_previous(self):
        """Previous in history"""
        if self.state.history and self.state.history_index > 0:
            self.state.history_index -= 1
            self.state.input_buffer = self.state.history[self.state.history_index]
    
    def _history_next(self):
        """Next in history"""
        if self.state.history_index < len(self.state.history) - 1:
            self.state.history_index += 1
            self.state.input_buffer = self.state.history[self.state.history_index]
        else:
            self.state.input_buffer = ""
    
    def _render(self):
        """Render the UI"""
        clear_screen()
        
        self._draw_header()
        
        self._draw_messages()
        
        self._draw_input_prompt()
        
        self._draw_status()
        
        move_cursor(1, self.height)
    
    def _draw_header(self):
        """Draw header bar"""
        width = self.width
        
        cat_icon = style("🐱", color="cyan")
        title = style(" Galaxy Destroyer ", bold=True, color="white", bg_color="black")
        model = style(f" {self.context.model} ", color="gray", dim=True)
        
        sep = style("│", color="gray")
        
        cwd = style(f" {self.context.cwd[:30]} ", color="gray", dim=True)
        
        header = cat_icon + " " + title + sep + model + sep + cwd
        
        write_line(header[:width])
        write_line(style("─" * width, color="gray", dim=True))
    
    def _draw_messages(self):
        """Draw chat messages"""
        max_lines = self.height - 8
        
        start = max(0, len(self.messages) - max_lines)
        
        for msg in self.messages[start:]:
            if msg.role == "user":
                write_line(style(f"  > {msg.content}", color="yellow"))
            elif msg.role == "assistant":
                lines = msg.content.split('\n')
                for line in lines[:50]:
                    write_line(style(f"  {line}", color="white"))
            elif msg.role == "tool":
                write_line(style(f"  [Tool] {msg.content[:200]}", color="cyan", dim=True))
            elif msg.role == "system":
                write_line(style(f"  {msg.content}", color="gray"))
            elif msg.role == "help":
                for line in msg.content.split('\n'):
                    if line.strip():
                        write_line(style(f"  {line}", color="green"))
        
        write_line("")
    
    def _draw_input_prompt(self):
        """Draw input line"""
        write_line(style("─" * self.width, color="gray", dim=True))
        
        prompt = style("🐱 ", color="cyan", bold=True)
        
        if self._loading:
            prompt = style("💭 ", color="yellow", bold=True)
            write(prompt + style(self._loading_text, color="gray", dim=True))
        else:
            write(prompt + self.state.input_buffer)
        
        if self.state.cursor_pos < len(self.state.input_buffer):
            move_cursor(len(prompt) + self.state.cursor_pos + 3, self.height - 2)
    
    def _draw_status(self):
        """Draw status bar"""
        write_line("")
        
        status_parts = [
            style("NEW", color="cyan"),
            f"msgs: {len(self.messages)}",
            f"history: {len(self.state.history)}",
        ]
        
        if self._loading:
            status_parts.append(style("● Thinking...", color="yellow"))
        
        if os.environ.get("ANTHROPIC_API_KEY"):
            status_parts.append(style("● API Ready", color="green"))
        else:
            status_parts.append(style("○ No API Key", color="red"))
        
        status = "  ".join(status_parts)
        
        write_line(status)
    
    def _show_exit(self):
        """Show exit message"""
        clear_screen()
        
        exit_box = [
            "",
            style("  ╔══════════════════════════════════════════════════╗", color="cyan"),
            style("  ║          Thanks for using Galaxy Destroyer!     ║", color="cyan"),
            style("  ║                   See you next time!              ║", color="white"),
            style("  ╚══════════════════════════════════════════════════╝", color="cyan"),
            "",
        ]
        
        for line in exit_box:
            write_line(line)
    
    def _cleanup(self):
        """Cleanup on exit"""
        write_line("")


def main():
    """Main entry"""
    tui = BeautifulTUI()
    tui.run()


if __name__ == "__main__":
    main()