"""Enhanced TUI - Beautiful Claude Code-like interface with full features"""

import os
import sys
import time
import asyncio
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from core.render import (
    get_terminal_size, clear_screen, move_cursor, write, write_line,
    style, BorderStyle, DOUBLE_BORDER, ROUNDED_BORDER, word_wrap
)
from core.state import Context, State, Color
from core.app import InputHandler, Key
from core.bootstrap import format_status


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = 0
    tool_use: Optional[Dict] = None
    thinking: bool = False


@dataclass
class ToolUse:
    name: str
    input_data: Dict
    status: str = "running"
    result: Optional[str] = None


class MessageType(Enum):
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SYSTEM = "system"


class BeautifulTUI:
    """Beautiful Claude Code-like terminal UI with full features"""
    
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
        self._loading_dots = 0
        self._tool_uses: List[ToolUse] = []
        self._show_sidebar = False
        self._sidebar_content: List[str] = []
        self._input_line = 0
        self._thinking = False
        self._thinking_text = ""
        self._status_bar_items: List[str] = []
        self._keybindings_mode = False
        self._vim_mode = False
        self._command_mode = False
        self._search_mode = False
        self._search_query = ""
    
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
        except Exception as e:
            self._show_error(str(e))
        finally:
            self._cleanup()
    
    def _setup(self):
        """Setup terminal"""
        if os.name == 'nt':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        self.context.cwd = os.getcwd()
        self._update_status_bar()
    
    def _update_status_bar(self):
        """Update status bar items"""
        self._status_bar_items = [
            f"cwd: {os.path.basename(self.context.cwd)}",
            f"backend: {self.context.backend}",
            f"model: {self.context.model}",
        ]
    
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
            style("   ╔═══════════════════════════════════════════════════╗", color="cyan"),
            style("   ║        Galaxy Destroyer v0.1.0                   ║", color="cyan", bold=True),
            style("   ║        AI-Powered Terminal Assistant             ║", dim=True),
            style("   ╚═══════════════════════════════════════════════════╝", color="cyan"),
            "",
            style("   Getting Started:", bold=True, color="yellow"),
            "",
            "   " + style("ask <message>", color="green") + "  - Chat with AI",
            "   " + style("tool <name>", color="green") + "   - Run a tool directly",
            "   " + style("run <cmd>", color="green") + "    - Execute shell command",
            "   " + style("agents", color="green") + "       - List available agents",
            "   " + style("tasks", color="green") + "        - List tasks",
            "   " + style("clear", color="green") + "        - Clear conversation",
            "   " + style("help", color="green") + "         - Show all commands",
            "",
            style("   Shortcuts:", bold=True, color="yellow"),
            "",
            "   " + style("Ctrl+C", color="magenta") + "     - Exit",
            "   " + style("Ctrl+L", color="magenta") + "     - Clear screen",
            "   " + style("Ctrl+G", color="magenta") + "     - Toggle sidebar",
            "   " + style("Ctrl+T", color="magenta") + "     - Toggle thinking",
            "   " + style("Tab", color="magenta") + "       - Autocomplete",
            "",
            style("   Default: OpenCode.ai backend (no API key needed!)", dim=True, color="gray"),
            "",
        ]
        
        for line in welcome_box:
            write_line(line)
        
        self._draw_input_prompt()
        move_cursor(1, self.height)
    
    def _main_loop(self):
        """Main loop"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if self._needs_render:
                self._render()
                self._needs_render = False
            
            if self._loading:
                if current_time - last_time > 0.5:
                    self._loading_dots = (self._loading_dots + 1) % 4
                    last_time = current_time
                    self._render_loading()
            
            key = self.input_handler.read_key()
            
            if key:
                self._handle_key(key)
                self._needs_render = True
            else:
                time.sleep(0.01)
    
    def _render_loading(self):
        """Render loading indicator"""
        dots = "." * self._loading_dots
        loading_text = f" {self._loading_text}{dots}"
        move_cursor(1, self.height - 1)
        write(" " * self.width)
        move_cursor(1, self.height - 1)
        write(style(loading_text, color="cyan", blink=True))
    
    def _handle_key(self, key: Key):
        """Handle key press"""
        if key.name == "ctrl_c":
            if self.state.input_buffer:
                self.state.input_buffer = ""
                self._render_input_line()
            else:
                self.running = False
            return
        
        if key.name == "escape":
            if self._vim_mode:
                self._vim_mode = False
                self.state.mode = "normal"
            self._keybindings_mode = False
            self._search_mode = False
            return
        
        if key.name == "ctrl_l":
            clear_screen()
            self._render()
            return
        
        if key.name == "ctrl_g":
            self._show_sidebar = not self._show_sidebar
            return
        
        if key.name == "ctrl_t":
            self._thinking = not self._thinking
            return
        
        if key.name == "ctrl_u":
            self.state.input_buffer = ""
            self._render_input_line()
            return
        
        if key.name == "ctrl_w":
            words = self.state.input_buffer.split()
            if words:
                self.state.input_buffer = self.state.input_buffer[:-len(words[-1]) - 1]
            self._render_input_line()
            return
        
        if key.name == "enter":
            self._execute_input()
            return
        
        if key.name == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
                self._render_input_line()
            return
        
        if key.name == "up":
            self._history_previous()
            return
        
        if key.name == "down":
            self._history_next()
            return
        
        if key.name == "left":
            return
        
        if key.name == "right":
            return
        
        if key.name == "tab":
            self._handle_tab_complete()
            return
        
        if key.name == "home":
            self.state.input_buffer = ""
            self._render_input_line()
            return
        
        if len(key.value) == 1 and not key.meta:
            self.state.input_buffer += key.value
            self._render_input_line()
    
    def _render_input_line(self):
        """Render the input line"""
        move_cursor(1, self.height)
        write(" " * self.width)
        move_cursor(1, self.height)
        
        prompt = style("> ", color="green", bold=True)
        input_text = self.state.input_buffer
        
        if self._thinking:
            prompt = style("◌ ", color="cyan", blink=True)
        
        write(prompt + input_text)
    
    def _execute_input(self):
        """Execute input command"""
        cmd = self.state.input_buffer.strip()
        
        if not cmd:
            write_line("")
            self._draw_input_prompt()
            return
        
        self.state.add_to_history(cmd)
        self.state.input_buffer = ""
        
        self._add_message("user", cmd)
        
        self._process_command(cmd)
    
    def _process_command(self, cmd: str):
        """Process user command"""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ("ask", "chat", "ai"):
            self._handle_aiAsk(args)
        elif command == "help":
            self._show_help()
        elif command == "clear":
            self.messages.clear()
            clear_screen()
            self._render()
        elif command in ("exit", "quit", "q"):
            self.running = False
        elif command == "status":
            self._show_status()
        elif command == "tools":
            self._list_tools()
        elif command == "agents":
            self._list_agents()
        elif command == "tasks":
            self._list_tasks()
        elif command == "run" or command == "!":
            self._run_shell(args)
        elif command == "tool":
            self._run_tool(args)
        else:
            self._handle_aiAsk(cmd)
    
    def _handle_aiAsk(self, prompt: str):
        """Handle AI ask command"""
        if not prompt:
            self._add_message("system", "Usage: ask <message>")
            return
        
        self._loading = True
        self._loading_text = "Thinking"
        
        thread = threading.Thread(target=self._async_ai_ask, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _async_ai_ask(self, prompt: str):
        """Async AI ask in background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._call_ai(prompt))
        except Exception as e:
            self._add_message("error", str(e))
        finally:
            self._loading = False
            self._needs_render = True
    
    async def _call_ai(self, prompt: str):
        """Call AI API"""
        from services.api import create_client, Backend
        from services.tools import get_executor
        
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
            self._add_tool_use(tool_use.name, tool_use.input)
            try:
                result = await executor.execute_tool(
                    name=tool_use.name,
                    tool_use_id=tool_use.id,
                    input_data=tool_use.input,
                    context=self.context
                )
                self._complete_tool_use(tool_use.name, result.content if result.content else result.error)
                return result
            except Exception as e:
                self._complete_tool_use(tool_use.name, str(e), error=True)
                return {"error": str(e)}
        
        try:
            from core.bootstrap import build_full_system_prompt
            system_prompt = build_full_system_prompt(self.context.model, self.context.backend)
            
            response = await client.send_message(
                system_prompt=system_prompt,
                tools=tools_schema,
                on_tool_use=on_tool
            )
            
            self._add_message("assistant", response.message.content)
            
        except Exception as e:
            self._add_message("error", str(e))
        
        self._needs_render = True
    
    def _add_message(self, role: str, content: str):
        """Add a message to the chat"""
        msg = ChatMessage(role=role, content=content, timestamp=time.time())
        self.messages.append(msg)
        self._render_messages()
    
    def _add_tool_use(self, name: str, input_data: Dict):
        """Add a tool use to display"""
        tool_use = ToolUse(name=name, input_data=input_data, status="running")
        self._tool_uses.append(tool_use)
        self._render_messages()
    
    def _complete_tool_use(self, name: str, result: str, error: bool = False):
        """Complete a tool use"""
        for tool in self._tool_uses:
            if tool.name == name and tool.status == "running":
                tool.status = "completed" if not error else "error"
                tool.result = result
                break
        self._render_messages()
    
    def _show_help(self):
        """Show help"""
        help_text = """
=== Galaxy Destroyer Commands ===

AI & Chat:
  ask <msg>      - Chat with AI
  chat          - Start conversation mode
  agents        - List available agents

Tools:
  tool <name>   - Run a specific tool
  tools         - List all tools

Shell:
  run <cmd>     - Execute shell command
  !<cmd>        - Execute shell command (shortcut)

Tasks:
  task create   - Create a new task
  task list     - List all tasks

Other:
  status        - Show current status
  clear         - Clear conversation
  help          - Show this help
  exit          - Exit
"""
        self._add_message("system", help_text)
    
    def _show_status(self):
        """Show status"""
        status = format_status(self.context.model, self.context.backend)
        self._add_message("system", status)
    
    def _list_tools(self):
        """List tools"""
        from services.tools import get_executor
        executor = get_executor()
        tools = sorted(executor.list_tools())
        
        msg = "Available tools:\n" + "\n".join(f"  - {t}" for t in tools)
        self._add_message("system", msg)
    
    def _list_agents(self):
        """List agents"""
        from services.agents import list_agents
        agents = list_agents()
        
        msg = "Available agents:\n"
        for name, desc in agents.items():
            msg += f"  {name}: {desc}\n"
        
        self._add_message("system", msg)
    
    def _list_tasks(self):
        """List tasks"""
        from services.tasks import task_list
        result = task_list()
        
        msg = f"Tasks ({result.get('count', 0)}):\n"
        for task in result.get('tasks', [])[:10]:
            status_icon = "○" if task['status'] == 'pending' else "◉" if task['status'] == 'in_progress' else "✓"
            msg += f"  {status_icon} {task.get('title', 'Untitled')}\n"
        
        self._add_message("system", msg)
    
    def _run_shell(self, cmd: str):
        """Run shell command"""
        if not cmd:
            return
        
        import subprocess
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr or "(no output)"
            self._add_message("system", f"$ {cmd}\n{output}")
        except Exception as e:
            self._add_message("error", f"Error: {str(e)}")
    
    def _run_tool(self, args: str):
        """Run a tool"""
        if not args:
            self._add_message("system", "Usage: tool <name> [args...]")
            return
        
        parts = args.split()
        tool_name = parts[0]
        tool_args = {}
        
        for arg in parts[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                tool_args[key] = value
        
        async def run():
            from services.tools import get_executor
            executor = get_executor()
            return await executor.execute_tool(
                name=tool_name,
                tool_use_id="tui",
                input_data=tool_args,
                context=self.context
            )
        
        result = asyncio.run(run())
        output = result.content if result.content else result.error
        self._add_message("system", f"Tool: {tool_name}\n{output}")
    
    def _handle_tab_complete(self):
        """Handle tab completion"""
        partial = self.state.input_buffer
        
        from commands import get_commands
        registry = get_commands()
        
        if partial.startswith('/'):
            partial = partial[1:]
        
        cmds = registry.search(partial)
        
        if cmds:
            cmd = cmds[0].name
            if not partial:
                self.state.input_buffer = f"/{cmd} "
            else:
                self.state.input_buffer = cmd
        
        self._render_input_line()
    
    def _history_previous(self):
        """Go to previous history item"""
        if self.state.history:
            if self.state.history_index < len(self.state.history) - 1:
                self.state.history_index += 1
            idx = len(self.state.history) - 1 - self.state.history_index
            if idx >= 0:
                self.state.input_buffer = self.state.history[idx]
                self._render_input_line()
    
    def _history_next(self):
        """Go to next history item"""
        if self.state.history and self.state.history_index > 0:
            self.state.history_index -= 1
            idx = len(self.state.history) - 1 - self.state.history_index
            if idx >= 0:
                self.state.input_buffer = self.state.history[idx]
                self._render_input_line()
        else:
            self.state.history_index = -1
            self.state.input_buffer = ""
            self._render_input_line()
    
    def _render(self):
        """Render the UI"""
        clear_screen()
        self._draw_header()
        self._render_messages()
        self._draw_input_prompt()
        self._draw_status_bar()
        self._render_input_line()
    
    def _render_messages(self):
        """Render messages"""
        start_row = 3
        
        move_cursor(1, start_row)
        
        for msg in self.messages[-20:]:
            if msg.role == "user":
                line = style("You: ", color="green", bold=True) + msg.content[:100]
            elif msg.role == "assistant":
                line = style("Galaxy: ", color="cyan", bold=True) + msg.content[:100]
            elif msg.role == "error":
                line = style("Error: ", color="red", bold=True) + msg.content[:100]
            else:
                line = style(msg.content, dim=True)
            
            write_line(line[:self.width - 2])
        
        for tool in self._tool_uses[-5:]:
            status_color = "green" if tool.status == "completed" else "yellow" if tool.status == "running" else "red"
            line = f"  ◉ {style(tool.name, color=status_color)}"
            if tool.result:
                line += f" → {tool.result[:50]}..."
            write_line(line)
    
    def _draw_header(self):
        """Draw header"""
        header = style(" Galaxy Destroyer ", bg_color="blue", color="white", bold=True)
        write(header.ljust(self.width))
        write_line("")
    
    def _draw_input_prompt(self):
        """Draw input prompt"""
        move_cursor(1, self.height - 1)
        write(" " * self.width)
        move_cursor(1, self.height - 1)
        prompt = style("> ", color="green", bold=True)
        write(prompt)
    
    def _draw_status_bar(self):
        """Draw status bar"""
        move_cursor(1, self.height)
        
        status_parts = [
            f"cwd: {os.path.basename(self.context.cwd)}",
            f"{self.context.backend}:{self.context.model}",
        ]
        
        if self._loading:
            status_parts.append(style("◌", color="cyan", blink=True) + " thinking")
        
        if self._vim_mode:
            status_parts.append(style("VIM", color="magenta"))
        
        status = " | ".join(status_parts)
        
        status = status.rjust(self.width)
        write(status)
    
    def _show_exit(self):
        """Show exit message"""
        clear_screen()
        write_line("")
        write_line(style("   Thanks for using Galaxy Destroyer!", color="cyan", bold=True))
        write_line(style("   See you next time!", color="gray"))
        write_line("")
    
    def _show_error(self, error: str):
        """Show error"""
        clear_screen()
        write_line("")
        write_line(style(f"   Error: {error}", color="red", bold=True))
        write_line("")
    
    def _cleanup(self):
        """Cleanup on exit"""
        pass