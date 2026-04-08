"""Enhanced TUI - Full Claude Code-like interface"""

import os
import sys
import time
import asyncio
import threading
import subprocess
from typing import Optional, List, Dict, Any
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


class SidebarPanel(Enum):
    SESSION = "session"
    TOOLS = "tools"
    FILES = "files"
    GIT = "git"
    HELP = "help"


class BeautifulTUI:
    """Full-featured Claude Code-like terminal UI"""
    
    def __init__(self):
        self.context = Context()
        self.state = State()
        self.input_handler = InputHandler()
        self.messages: List[ChatMessage] = []
        self.running = False
        self.width = 80
        self.height = 24
        self.sidebar_width = 25
        self._needs_render = True
        self._loading = False
        self._loading_text = ""
        self._loading_dots = 0
        self._tool_uses: List[ToolUse] = []
        self._show_sidebar = True
        self._sidebar_panel = SidebarPanel.SESSION
        self._input_line = 0
        self._thinking = False
        self._status_bar_items: List[str] = []
        self._search_mode = False
        self._search_query = ""
        self._autocomplete_options: List[str] = []
        self._autocomplete_index = 0
        self._file_tree_cache = {}
    
    def run(self):
        """Main run loop"""
        self.running = True
        self.width, self.height = get_terminal_size()
        self._ensure_width()
        
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
    
    def _ensure_width(self):
        """Ensure minimum width"""
        if self.width < 60:
            self.width = 60
    
    def _setup(self):
        """Setup terminal"""
        if os.name == 'nt':
            import msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        self.context.cwd = os.getcwd()
        self._update_status_bar()
        self._refresh_file_tree()
    
    def _update_status_bar(self):
        """Update status bar"""
        self._status_bar_items = [
            f"cwd: {os.path.basename(self.context.cwd)}",
            f"{self.context.backend}:{self.context.model}",
        ]
    
    def _refresh_file_tree(self):
        """Refresh file tree cache"""
        try:
            tree = self._build_file_tree(self.context.cwd, depth=2)
            self._file_tree_cache = tree
        except:
            self._file_tree_cache = {}
    
    def _build_file_tree(self, path: str, depth: int = 2) -> Dict:
        """Build file tree"""
        tree = {"name": os.path.basename(path) or path, "type": "dir", "children": []}
        
        if depth <= 0:
            return tree
        
        try:
            entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x))
            for entry in entries[:15]:
                if entry.startswith('.'):
                    continue
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    tree["children"].append(self._build_file_tree(entry_path, depth - 1))
                else:
                    tree["children"].append({"name": entry, "type": "file"})
        except:
            pass
        
        return tree
    
    def _show_welcome(self):
        """Show welcome banner"""
        clear_screen()
        self._render()
    
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
        
        content_width = self.width - self.sidebar_width - 1 if self._show_sidebar else self.width
        
        move_cursor(1, self.height - 1)
        write(" " * content_width)
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
            self._search_mode = False
            self._autocomplete_options = []
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
        
        if key.name == "ctrl_s":
            self._cycle_sidebar_panel()
            return
        
        if key.name == "ctrl_f":
            self._toggle_file_tree()
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
            if self._autocomplete_options:
                self._select_autocomplete()
            else:
                self._execute_input()
            return
        
        if key.name == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
                self._update_autocomplete()
                self._render_input_line()
            return
        
        if key.name == "up":
            if self._autocomplete_options:
                self._autocomplete_index = (self._autocomplete_index - 1) % len(self._autocomplete_options)
                self._render_autocomplete()
            else:
                self._history_previous()
            return
        
        if key.name == "down":
            if self._autocomplete_options:
                self._autocomplete_index = (self._autocomplete_index + 1) % len(self._autocomplete_options)
                self._render_autocomplete()
            else:
                self._history_next()
            return
        
        if key.name == "tab":
            if self._autocomplete_options:
                self._select_autocomplete()
            else:
                self._handle_tab_complete()
            return
        
        if key.name == "ctrl_r":
            self._toggle_search()
            return
        
        if len(key.value) == 1 and not key.meta:
            self.state.input_buffer += key.value
            self._update_autocomplete()
            self._render_input_line()
    
    def _cycle_sidebar_panel(self):
        """Cycle through sidebar panels"""
        panels = list(SidebarPanel)
        idx = panels.index(self._sidebar_panel)
        self._sidebar_panel = panels[(idx + 1) % len(panels)]
    
    def _toggle_file_tree(self):
        """Toggle file tree panel"""
        if self._sidebar_panel == SidebarPanel.FILES:
            self._sidebar_panel = SidebarPanel.SESSION
        else:
            self._sidebar_panel = SidebarPanel.FILES
            self._refresh_file_tree()
    
    def _toggle_search(self):
        """Toggle search mode"""
        self._search_mode = not self._search_mode
        if self._search_mode:
            self._search_query = ""
    
    def _update_autocomplete(self):
        """Update autocomplete options"""
        partial = self.state.input_buffer.lower()
        
        if not partial or len(partial) < 2:
            self._autocomplete_options = []
            return
        
        commands = [
            "ask", "agents", "clear", "config", "exit", "help", "run", 
            "status", "task", "tasks", "tool", "tools", "chat"
        ]
        
        tools = []
        try:
            from services.tools import get_executor
            executor = get_executor()
            tools = executor.list_tools()
        except:
            pass
        
        options = commands + tools
        
        self._autocomplete_options = [o for o in options if o.startswith(partial)]
        self._autocomplete_index = 0
    
    def _render_autocomplete(self):
        """Render autocomplete options"""
        if not self._autocomplete_options:
            return
        
        content_width = self.width - self.sidebar_width - 1 if self._show_sidebar else self.width
        move_cursor(1, self.height - 3)
        write(" " * content_width)
        move_cursor(1, self.height - 3)
        
        options_text = " | ".join(self._autocomplete_options[:5])
        write(style(options_text, color="yellow", dim=True))
    
    def _select_autocomplete(self):
        """Select autocomplete option"""
        if self._autocomplete_options:
            selected = self._autocomplete_options[self._autocomplete_index]
            
            if ' ' not in self.state.input_buffer:
                self.state.input_buffer = selected + " "
            else:
                self.state.input_buffer = selected
            
            self._autocomplete_options = []
            self._render_input_line()
    
    def _render_input_line(self):
        """Render the input line"""
        content_width = self.width - self.sidebar_width - 1 if self._show_sidebar else self.width
        
        move_cursor(1, self.height - 1)
        write(" " * content_width)
        move_cursor(1, self.height - 1)
        
        prompt = style("> ", color="green", bold=True)
        input_text = self.state.input_buffer[:content_width - 2]
        
        if self._thinking:
            prompt = style("◌ ", color="cyan", blink=True)
        
        if self._search_mode:
            prompt = style("/", color="yellow")
            input_text = self._search_query + "_"
        
        write(prompt + input_text)
        
        if self._autocomplete_options:
            self._render_autocomplete()
    
    def _execute_input(self):
        """Execute input command"""
        if self._search_mode:
            self._perform_search()
            return
        
        cmd = self.state.input_buffer.strip()
        
        if not cmd:
            write_line("")
            self._draw_input_prompt()
            return
        
        self.state.add_to_history(cmd)
        self.state.input_buffer = ""
        
        self._add_message("user", cmd)
        self._process_command(cmd)
    
    def _perform_search(self):
        """Perform search in messages"""
        query = self.state.input_buffer.strip()
        self._search_query = query
        self._search_mode = False
        
        if query:
            results = [m for m in self.messages if query.lower() in m.content.lower()]
            
            msg = f"Found {len(results)} results for '{query}':\n"
            for m in results[:5]:
                msg += f"  {m.role}: {m.content[:50]}...\n"
            
            self._add_message("system", msg)
    
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
        elif command == "cd":
            self._change_directory(args)
        else:
            self._handle_aiAsk(cmd)
    
    def _change_directory(self, path: str):
        """Change directory"""
        if not path:
            path = os.path.expanduser("~")
        
        try:
            os.chdir(path)
            self.context.cwd = os.getcwd()
            self._refresh_file_tree()
            self._update_status_bar()
            self._add_message("system", f"Changed directory to: {self.context.cwd}")
        except Exception as e:
            self._add_message("error", f"Error: {str(e)}")
    
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
        """Async AI ask"""
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
        """Call AI"""
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
        """Add message"""
        msg = ChatMessage(role=role, content=content, timestamp=time.time())
        self.messages.append(msg)
        self._render_messages()
    
    def _add_tool_use(self, name: str, input_data: Dict):
        """Add tool use"""
        tool_use = ToolUse(name=name, input_data=input_data, status="running")
        self._tool_uses.append(tool_use)
        self._render_messages()
    
    def _complete_tool_use(self, name: str, result: str, error: bool = False):
        """Complete tool use"""
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
  agents        - List agents

Tools & Shell:
  tool <name>   - Run tool
  tools         - List tools
  run <cmd>     - Execute shell
  !<cmd>        - Shell shortcut

Navigation:
  cd <dir>      - Change directory

Tasks:
  task create   - Create task
  task list     - List tasks

Session:
  status        - Show status
  clear         - Clear chat

=== Keyboard Shortcuts ===
  Ctrl+C   Exit
  Ctrl+L   Clear screen
  Ctrl+G   Toggle sidebar
  Ctrl+S   Cycle sidebar panel
  Ctrl+F   File tree
  Ctrl+R   Search
  Ctrl+T   Toggle thinking
  Up/Down  History
  Tab      Autocomplete
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
        
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr or "(no output)"
            self._add_message("system", f"$ {cmd}\n{output}")
        except Exception as e:
            self._add_message("error", f"Error: {str(e)}")
    
    def _run_tool(self, args: str):
        """Run tool"""
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
        """Tab completion"""
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
                self.state.input_buffer = cmd + " "
        
        self._render_input_line()
    
    def _history_previous(self):
        """History previous"""
        if self.state.history:
            if self.state.history_index < len(self.state.history) - 1:
                self.state.history_index += 1
            idx = len(self.state.history) - 1 - self.state.history_index
            if idx >= 0:
                self.state.input_buffer = self.state.history[idx]
                self._render_input_line()
    
    def _history_next(self):
        """History next"""
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
        """Render UI"""
        clear_screen()
        
        content_width = self.width - self.sidebar_width - 1 if self._show_sidebar else self.width
        
        self._draw_header(content_width)
        self._render_messages(content_width)
        self._draw_input_prompt(content_width)
        self._draw_status_bar(content_width)
        
        if self._show_sidebar:
            self._render_sidebar()
        
        self._render_input_line()
    
    def _render_messages(self, width: int):
        """Render messages"""
        start_row = 3
        
        move_cursor(1, start_row)
        
        for msg in self.messages[-20:]:
            if msg.role == "user":
                line = style("You: ", color="green", bold=True) + msg.content[:width-10]
            elif msg.role == "assistant":
                line = style("Galaxy: ", color="cyan", bold=True) + msg.content[:width-10]
            elif msg.role == "error":
                line = style("Error: ", color="red", bold=True) + msg.content[:width-10]
            else:
                line = style(msg.content[:width-5], dim=True)
            
            write_line(line[:width - 2])
        
        for tool in self._tool_uses[-5:]:
            status_color = "green" if tool.status == "completed" else "yellow" if tool.status == "running" else "red"
            line = f"  ◉ {style(tool.name, color=status_color)}"
            if tool.result:
                line += f" → {tool.result[:30]}..."
            write_line(line[:width - 2])
    
    def _render_sidebar(self):
        """Render sidebar"""
        sidebar_x = self.width - self.sidebar_width + 1
        
        move_cursor(sidebar_x, 1)
        write(style("│", color="gray"))
        
        for i in range(2, self.height):
            move_cursor(sidebar_x, i)
            write(style("│", color="gray"))
        
        if self._sidebar_panel == SidebarPanel.SESSION:
            self._render_session_panel(sidebar_x)
        elif self._sidebar_panel == SidebarPanel.TOOLS:
            self._render_tools_panel(sidebar_x)
        elif self._sidebar_panel == SidebarPanel.FILES:
            self._render_files_panel(sidebar_x)
        elif self._sidebar_panel == SidebarPanel.GIT:
            self._render_git_panel(sidebar_x)
        elif self._sidebar_panel == SidebarPanel.HELP:
            self._render_help_panel(sidebar_x)
    
    def _render_session_panel(self, x: int):
        """Render session panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" Session ", bg_color="blue", color="white", bold=True))
        
        y += 2
        move_cursor(x, y)
        write(style(f"Dir:", color="gray"))
        move_cursor(x + 5, y)
        write(os.path.basename(self.context.cwd)[:self.sidebar_width - 6])
        
        y += 1
        move_cursor(x, y)
        write(style(f"Backend:", color="gray"))
        move_cursor(x + 8, y)
        write(style(self.context.backend, color="cyan"))
        
        y += 1
        move_cursor(x, y)
        write(style(f"Model:", color="gray"))
        move_cursor(x + 7, y)
        write(self.context.model[:self.sidebar_width - 8])
        
        y += 2
        move_cursor(x, y)
        write(style(" Shortcuts ", bg_color="magenta", color="white"))
        
        shortcuts = [
            ("Ctrl+G", "Sidebar"),
            ("Ctrl+S", "Panel"),
            ("Ctrl+F", "Files"),
            ("Ctrl+R", "Search"),
            ("Ctrl+T", "Think"),
        ]
        
        y += 1
        for key, desc in shortcuts:
            move_cursor(x, y)
            write(style(f"{key}:", color="yellow"))
            move_cursor(x + 7, y)
            write(desc[:self.sidebar_width - 8])
            y += 1
    
    def _render_tools_panel(self, x: int):
        """Render tools panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" Tools ", bg_color="blue", color="white", bold=True))
        
        y += 2
        
        try:
            from services.tools import get_executor
            executor = get_executor()
            tools = sorted(executor.list_tools())[:20]
        except:
            tools = []
        
        for tool in tools[:self.height - 6]:
            move_cursor(x, y)
            write(f"  {tool[:self.sidebar_width - 4]}")
            y += 1
    
    def _render_files_panel(self, x: int):
        """Render files panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" Files ", bg_color="blue", color="white", bold=True))
        
        y += 1
        
        self._render_tree(x, y, self._file_tree_cache, 0)
    
    def _render_tree(self, x: int, y: int, node: Dict, indent: int):
        """Render file tree"""
        prefix = "  " * indent
        
        if node["type"] == "dir":
            move_cursor(x, y)
            write(prefix + style("📁 ", color="yellow") + node["name"][:self.sidebar_width - indent - 4])
            y += 1
            
            for child in node.get("children", [])[:5]:
                y = self._render_tree(x, y, child, indent + 1)
        else:
            move_cursor(x, y)
            write(prefix + style("📄 ", color="gray") + node["name"][:self.sidebar_width - indent - 4])
            y += 1
        
        return y
    
    def _render_git_panel(self, x: int):
        """Render git panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" Git ", bg_color="blue", color="white", bold=True))
        
        y += 2
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.context.cwd, capture_output=True, text=True
            )
            
            if result.stdout:
                changes = result.stdout.strip().split("\n")
                
                for change in changes[:self.height - 8]:
                    if change.startswith("M"):
                        write(style(" M ", color="yellow") + change[3:self.sidebar_width - 4])
                    elif change.startswith("A"):
                        write(style(" A ", color="green") + change[3:self.sidebar_width - 4])
                    elif change.startswith("D"):
                        write(style(" D ", color="red") + change[3:self.sidebar_width - 4])
                    else:
                        write(" " + change[:self.sidebar_width - 4])
                    y += 1
            else:
                move_cursor(x, y)
                write(style("No changes", color="gray"))
                y += 1
        except:
            move_cursor(x, y)
            write(style("Not a git repo", color="gray"))
            y += 1
        
        y += 1
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.context.cwd, capture_output=True, text=True
            )
            branch = result.stdout.strip() or "main"
            move_cursor(x, y)
            write(style(f"Branch: ", color="gray") + branch)
        except:
            pass
    
    def _render_help_panel(self, x: int):
        """Render help panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" Help ", bg_color="blue", color="white", bold=True))
        
        y += 2
        
        commands = [
            ("ask <msg>", "Chat with AI"),
            ("agents", "List agents"),
            ("tools", "List tools"),
            ("run <cmd>", "Run shell"),
            ("tool <n>", "Run tool"),
            ("cd <dir>", "Change dir"),
            ("task", "Task commands"),
            ("status", "Show status"),
            ("help", "Show help"),
            ("clear", "Clear chat"),
        ]
        
        for cmd, desc in commands:
            move_cursor(x, y)
            write(style(f"{cmd:<12}", color="cyan") + desc[:self.sidebar_width - 14])
            y += 1
    
    def _draw_header(self, width: int):
        """Draw header"""
        header = style(" Galaxy Destroyer ", bg_color="blue", color="white", bold=True)
        write(header.ljust(width))
        write_line("")
    
    def _draw_input_prompt(self, width: int):
        """Draw input prompt"""
        move_cursor(1, self.height - 1)
        write(" " * width)
        move_cursor(1, self.height - 1)
        prompt = style("> ", color="green", bold=True)
        write(prompt)
    
    def _draw_status_bar(self, width: int):
        """Draw status bar"""
        move_cursor(1, self.height)
        
        status_parts = [
            f"cwd: {os.path.basename(self.context.cwd)}",
            f"{self.context.backend}:{self.context.model}",
        ]
        
        if self._loading:
            status_parts.append(style("◌", color="cyan", blink=True) + " thinking")
        
        if self._show_sidebar:
            status_parts.append(style(f"[{self._sidebar_panel.value.upper()}]", color="magenta"))
        
        status = " | ".join(status_parts)
        status = status.ljust(width)
        write(status)
    
    def _show_exit(self):
        """Show exit"""
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
        """Cleanup"""
        pass