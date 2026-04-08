"""Beautiful TUI - Claude Code-style with animations"""

import os
import sys
import time
import asyncio
import threading
import subprocess
import random
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


def style(text: str, bold: bool = False, italic: bool = False, 
          underline: bool = False, color: Optional[str] = None,
          bg_color: Optional[str] = None, dim: bool = False,
          blink: bool = False, reverse: bool = False) -> str:
    """Style text with ANSI codes"""
    codes = []
    
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if italic:
        codes.append("3")
    if underline:
        codes.append("4")
    if blink:
        codes.append("5")
    if reverse:
        codes.append("7")
    
    color_codes = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "gray": "90", "grey": "90",
    }
    bg_color_codes = {
        "black": "40", "red": "41", "green": "42", "yellow": "43",
        "blue": "44", "magenta": "45", "cyan": "46", "white": "47",
    }
    
    if color:
        codes.append(color_codes.get(color, "37"))
    if bg_color:
        codes.append(bg_color_codes.get(bg_color, "49"))
    
    if codes:
        return f"\033[{';'.join(codes)}m{text}\033[0m"
    return text


def get_terminal_size():
    """Get terminal size"""
    try:
        if os.name == 'nt':
            from ctypes import windll, create_string_buffer
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            if res:
                import struct
                bufx, bufy, curx, cury, wattr = struct.unpack("hhhhH", csbi.raw)
                width = curx - csbi[0] + 1
                height = cury - csbi[1] + 1
                return width, height
    except:
        pass
    return 80, 24


def clear_screen():
    """Clear the screen"""
    if os.name == 'nt':
        os.system('cls')
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def move_cursor(x: int, y: int):
    """Move cursor to position"""
    sys.stdout.write(f"\033[{y};{x}H")
    sys.stdout.flush()


def write(text: str = ""):
    """Write text"""
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except:
        pass


def write_line(text: str = ""):
    """Write line"""
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except:
        pass


def erase_line():
    """Erase current line"""
    sys.stdout.write("\033[2K")
    sys.stdout.flush()


def word_wrap(text: str, width: int) -> List[str]:
    """Word wrap text"""
    words = text.split()
    lines = []
    current = ""
    
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = current + " " + word if current else word
        else:
            if current:
                lines.append(current)
            current = word
    
    if current:
        lines.append(current)
    
    return lines


def git_status(cwd: str = None):
    """Get git status"""
    if cwd is None:
        cwd = os.getcwd()
    
    result = {
        "is_repo": False,
        "branch": "main",
        "changes": [],
        "staged": [],
        "untracked": [],
    }
    
    try:
        is_git = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd, capture_output=True, text=True
        )
        
        if is_git.returncode != 0:
            return result
        
        result["is_repo"] = True
        
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, capture_output=True, text=True
        )
        result["branch"] = branch.stdout.strip() or "main"
        
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True
        )
        
        if status.stdout:
            for line in status.stdout.strip().split("\n"):
                if len(line) >= 3:
                    code = line[:2]
                    path = line[3:]
                    
                    result["changes"].append(path)
                    
                    if code[0] in ["M", "A", "D"]:
                        result["staged"].append(path)
                    if code[1] == "?":
                        result["untracked"].append(path)
    
    except:
        pass
    
    return result


class Context:
    """Simple context"""
    cwd = ""
    backend = "opencode"
    model = "qwen2.5-coder"


class State:
    """Simple state"""
    input_buffer = ""
    history = []
    history_index = -1


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = 0
    tool_use: Optional[Dict] = None
    expanded: bool = False


@dataclass
class ToolUse:
    name: str
    input_data: Dict
    status: str = "running"
    result: Optional[str] = None
    start_time: float = 0


class SidebarPanel(Enum):
    SESSION = "session"
    TOOLS = "tools"
    FILES = "files"
    GIT = "git"
    AGENTS = "agents"


class CatAnimation:
    """Animated cat ASCII art"""
    
    FRAMES = [
        """
      /\\_/\\  
     ( o.o ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( -.- ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( ^.^ ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( *. ) 
     (")_(") 
""",
    ]
    
    @staticmethod
    def render(frame: int = 0) -> str:
        return CatAnimation.FRAMES[frame % len(CatAnimation.FRAMES)]


class BeautifulTUI:
    """Beautiful Claude Code-like terminal UI with animations"""
    
    def __init__(self):
        self.context = Context()
        self.state = State()
        self.messages: List[ChatMessage] = []
        self.running = False
        self.width, self.height = get_terminal_size()
        self.sidebar_width = 28
        self._needs_render = True
        self._loading = False
        self._loading_text = ""
        self._loading_frame = 0
        self._tool_uses: List[ToolUse] = []
        self._show_sidebar = True
        self._sidebar_panel = SidebarPanel.SESSION
        self._thinking = False
        self._thinking_idx = 0
        self._last_think_update = 0
        self._cat_frame = 0
        self._last_cat_update = 0
        self._search_mode = False
        self._search_query = ""
        self._selected_message = -1
        self._animations_enabled = True
    
    def run(self):
        """Main run loop"""
        self.running = True
        self.width, self.height = get_terminal_size()
        self._ensure_minimum_size()
        
        try:
            self._setup()
            self._show_welcome_animated()
            self._main_loop()
        except KeyboardInterrupt:
            self._exit_animated()
        except Exception as e:
            self._show_error(str(e))
        finally:
            self._cleanup()
    
    def _ensure_minimum_size(self):
        """Ensure minimum terminal size"""
        if self.width < 80:
            self.width = 80
        if self.height < 20:
            self.height = 20
    
    def _setup(self):
        """Setup terminal"""
        if os.name == 'nt':
            try:
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            except:
                pass
        
        self.context.cwd = os.getcwd()
        self._hide_cursor()
    
    def _hide_cursor(self):
        """Hide cursor"""
        try:
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
        except:
            pass
    
    def _show_cursor(self):
        """Show cursor"""
        try:
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()
        except:
            pass
    
    def _show_welcome_animated(self):
        """Show animated welcome"""
        clear_screen()
        
        cat = CatAnimation.render(0)
        
        lines = [
            style(cat, color="cyan"),
            "",
            style("  ╔══════════════════════════════════════════════════════════════╗", color="cyan", bold=True),
            style("  ║", color="cyan") + style("     ★  GALAXY DESTROYER  ★                              ", color="white", bold=True, bg_color="blue").ljust(62) + style("║", color="cyan"),
            style("  ║", color="cyan") + style("       AI-Powered Terminal Assistant                      ", color="gray", dim=True).ljust(62) + style("║", color="cyan"),
            style("  ╚══════════════════════════════════════════════════════════════╝", color="cyan", bold=True),
            "",
            style("  Getting Started:", color="yellow", bold=True),
            "",
            style("    ask <msg>", color="green") + "    - Chat with AI",
            style("    agents", color="green") + "      - List agents",
            style("    tools", color="green") + "       - List tools",
            style("    run <cmd>", color="green") + "    - Execute shell",
            style("    task", color="green") + "        - Task management",
            "",
            style("  Keyboard Shortcuts:", color="yellow", bold=True),
            "",
            style("    Ctrl+G", color="magenta") + " - Toggle sidebar",
            style("    Ctrl+S", color="magenta") + " - Cycle panels",
            style("    Ctrl+L", color="magenta") + " - Clear screen",
            style("    Ctrl+R", color="magenta") + " - Search",
            style("    ↑/↓", color="magenta") + "    - History",
            style("    Tab", color="magenta") + "      - Autocomplete",
            "",
            style("  Default: OpenCode.ai backend (no API key needed!)", color="gray", dim=True),
            "",
        ]
        
        for line in lines:
            try:
                print(line)
            except:
                pass
            time.sleep(0.02)
        
        time.sleep(0.5)
    
    def _main_loop(self):
        """Main loop"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if self._needs_render:
                self._render()
                self._needs_render = False
            
            if self._loading and current_time - last_time > 0.1:
                self._loading_frame = (self._loading_frame + 1) % 8
                last_time = current_time
                self._render_loading()
            
            if self._thinking and current_time - self._last_think_update > 0.3:
                self._thinking_idx = (self._thinking_idx + 1) % 4
                self._last_think_update = current_time
                self._render_status_bar()
            
            key = self._read_key()
            
            if key:
                self._handle_key(key)
                self._needs_render = True
            else:
                time.sleep(0.02)
    
    def _read_key(self) -> Optional[str]:
        """Read key without blocking"""
        try:
            if os.name == 'nt':
                import msvcrt
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\r':
                        return "enter"
                    elif char == b'\x08':
                        return "backspace"
                    elif char == b'\x1b':
                        return "escape"
                    return char.decode('utf-8', errors='ignore')
            else:
                import select
                if select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char == '\n':
                        return "enter"
                    elif char == '\t':
                        return "tab"
                    elif char == '\x7f':
                        return "backspace"
                    elif char == '\x03':
                        return "ctrl_c"
                    return char
        except:
            pass
        
        return None
    
    def _render_loading(self):
        """Render loading spinner"""
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        spin = spinners[self._loading_frame]
        
        content_width = self.width - self.sidebar_width - 2
        
        pos_y = self.height - 1
        pos_x = 1
        
        move_cursor(pos_x, pos_y)
        erase_line()
        
        text = f" {spin} {self._loading_text}"
        write(style(text, color="cyan", bold=True))
    
    def _handle_key(self, key: str):
        """Handle key press"""
        if key == "ctrl_c":
            if self.state.input_buffer:
                self.state.input_buffer = ""
                self._render_input_line()
            else:
                self.running = False
            return
        
        if key == "escape":
            self._search_mode = False
            return
        
        if key == "ctrl_l":
            clear_screen()
            self._render()
            return
        
        if key == "ctrl_g":
            self._show_sidebar = not self._show_sidebar
            return
        
        if key == "ctrl_s":
            self._cycle_sidebar()
            return
        
        if key == "enter":
            self._execute_input()
            return
        
        if key == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
                self._render_input_line()
            return
        
        if key in ["up", "down"]:
            if key == "up":
                self._history_prev()
            else:
                self._history_next()
            return
        
        if len(key) == 1:
            self.state.input_buffer += key
            self._render_input_line()
    
    def _cycle_sidebar(self):
        """Cycle sidebar panel"""
        panels = list(SidebarPanel)
        idx = panels.index(self._sidebar_panel)
        self._sidebar_panel = panels[(idx + 1) % len(panels)]
    
    def _history_prev(self):
        """Previous history"""
        if self.state.history and self.state.history_index < len(self.state.history) - 1:
            self.state.history_index += 1
            idx = len(self.state.history) - 1 - self.state.history_index
            if idx >= 0:
                self.state.input_buffer = self.state.history[idx]
                self._render_input_line()
    
    def _history_next(self):
        """Next history"""
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
    
    def _execute_input(self):
        """Execute input"""
        cmd = self.state.input_buffer.strip()
        
        if not cmd:
            write_line("")
            self._draw_input_prompt(self.width - self.sidebar_width - 2 if self._show_sidebar else self.width)
            return
        
        self.state.add_to_history(cmd)
        self.state.input_buffer = ""
        
        self._add_message("user", cmd)
        self._process_command(cmd)
    
    def add_to_history(self, cmd: str):
        if cmd.strip():
            self.state.history.append(cmd)
        self.state.history_index = len(self.state.history)
    
    def _process_command(self, cmd: str):
        """Process command"""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ("ask", "ai"):
            self._handle_ai(args)
        elif command == "help":
            self._show_help()
        elif command == "clear":
            self.messages.clear()
            clear_screen()
            self._render()
        elif command in ("exit", "quit"):
            self.running = False
        elif command == "status":
            self._show_status()
        elif command == "tools":
            self._list_tools()
        elif command == "agents":
            self._list_agents()
        elif command == "run":
            self._run_shell(args)
        elif command == "tasks":
            self._list_tasks()
        else:
            self._handle_ai(cmd)
    
    def _handle_ai(self, prompt: str):
        """Handle AI"""
        if not prompt:
            self._add_message("system", "Usage: ask <message>")
            return
        
        self._loading = True
        self._loading_text = "Thinking"
        
        thread = threading.Thread(target=self._async_ai, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _async_ai(self, prompt: str):
        """Async AI call"""
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
        
        backend = Backend.OPENCODE
        api_key = os.environ.get("OPENCODE_API_KEY", "")
        
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
                self._complete_tool(tool_use.name, result.content if result.content else result.error)
                return result
            except Exception as e:
                self._complete_tool(tool_use.name, str(e), error=True)
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
        tool = ToolUse(name=name, input_data=input_data, start_time=time.time())
        self._tool_uses.append(tool)
        self._render_messages()
    
    def _complete_tool(self, name: str, result: str, error: bool = False):
        """Complete tool"""
        for tool in self._tool_uses:
            if tool.name == name and tool.status == "running":
                tool.status = "completed" if not error else "error"
                tool.result = result
                break
        self._render_messages()
    
    def _show_help(self):
        """Show help"""
        self._add_message("system", """
╔══════════════════════════════════════════════════════════════╗
║                    Galaxy Destroyer Commands                  ║
╚══════════════════════════════════════════════════════════════╝

AI & Chat:
  ask <msg>      - Chat with AI
  agents        - List available agents

Tools & Shell:
  tools         - List all tools
  tool <name>   - Run a specific tool
  run <cmd>     - Execute shell command
  !<cmd>        - Execute shell (shortcut)

Tasks:
  task list     - List all tasks
  task create   - Create new task
  task update   - Update task status

Session:
  status        - Show current status
  clear         - Clear conversation
  help          - Show this help
  exit          - Exit

Keyboard Shortcuts:
  Ctrl+G - Toggle sidebar    Ctrl+S - Cycle sidebar
  Ctrl+L - Clear screen      Ctrl+R - Search
  ↑/↓   - Command history    Tab    - Autocomplete
""")
    
    def _show_status(self):
        """Show status"""
        status = f"""
╔══════════════════════════════════════════════════════════════╗
║                       Status Information                       ║
╚══════════════════════════════════════════════════════════════╝

  Backend:  {self.context.backend}
  Model:    {self.context.model}
  CWD:      {self.context.cwd}
  Messages: {len(self.messages)}
  Tools:    {len(self._tool_uses)}
"""
        self._add_message("system", status)
    
    def _list_tools(self):
        """List tools"""
        from services.tools import get_executor
        executor = get_executor()
        tools = sorted(executor.list_tools())
        
        msg = "╔══════════════════════════════════════════════════════════════╗\n"
        msg += "║                       Available Tools                         ║\n"
        msg += "╚══════════════════════════════════════════════════════════════╝\n"
        
        for tool in tools[:30]:
            msg += f"  {tool}\n"
        
        self._add_message("system", msg)
    
    def _list_agents(self):
        """List agents"""
        from services.agents import list_agents
        agents = list_agents()
        
        msg = "╔══════════════════════════════════════════════════════════════╗\n"
        msg += "║                       Available Agents                         ║\n"
        msg += "╚══════════════════════════════════════════════════════════════╝\n"
        
        for name, desc in agents.items():
            msg += f"  {name}: {desc[:60]}...\n"
        
        self._add_message("system", msg)
    
    def _list_tasks(self):
        """List tasks"""
        from services.tasks import task_list
        result = task_list()
        
        msg = f"Tasks ({result.get('count', 0)}):\n"
        
        for task in result.get('tasks', [])[:10]:
            status = "○" if task['status'] == 'pending' else "◉" if task['status'] == 'in_progress' else "✓"
            msg += f"  {status} {task.get('title', 'Untitled')}\n"
        
        self._add_message("system", msg)
    
    def _run_shell(self, cmd: str):
        """Run shell"""
        if not cmd:
            return
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr or "(no output)"
            self._add_message("system", f"$ {cmd}\n{output[:500]}")
        except Exception as e:
            self._add_message("error", f"Error: {str(e)}")
    
    def _render(self):
        """Render full UI"""
        clear_screen()
        
        content_width = self.width - self.sidebar_width - 2 if self._show_sidebar else self.width
        
        self._draw_header(content_width)
        self._render_messages(content_width)
        self._draw_input_prompt(content_width)
        self._draw_status_bar(content_width)
        
        if self._show_sidebar:
            self._render_sidebar()
        
        self._render_input_line()
    
    def _render_messages(self, width: int):
        """Render messages"""
        start = 3
        
        move_cursor(1, start)
        
        for msg in self.messages[-15:]:
            if msg.role == "user":
                write_line(style("  ✦ You ", color="green", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="white"))
            elif msg.role == "assistant":
                write_line(style("  ✦ Galaxy ", color="cyan", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="gray"))
            elif msg.role == "error":
                write_line(style("  ✦ Error ", color="red", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="red"))
            else:
                for line in word_wrap(msg.content, width - 2):
                    write_line(style(line, color="gray", dim=True))
        
        for tool in self._tool_uses[-5:]:
            status_color = "green" if tool.status == "completed" else "yellow"
            icon = "✓" if tool.status == "completed" else "◉"
            write_line(style(f"  {icon} {tool.name}", color=status_color, bold=True))
    
    def _draw_header(self, width: int):
        """Draw header"""
        move_cursor(1, 1)
        
        header = style(" ✦ GALAXY DESTROYER ", bg_color="blue", color="white", bold=True)
        try:
            write(header.ljust(width))
        except:
            pass
        
        move_cursor(1, 2)
        try:
            write(style("─" * width, color="gray"))
        except:
            pass
    
    def _draw_input_prompt(self, width: int):
        """Draw input prompt"""
        y = self.height - 1
        move_cursor(1, y)
        erase_line()
        
        prompt = style(" ✦ ", color="cyan", bold=True)
        write(prompt)
    
    def _render_input_line(self):
        """Render input line"""
        width = self.width - self.sidebar_width - 2 if self._show_sidebar else self.width
        
        y = self.height - 1
        move_cursor(3, y)
        erase_line()
        
        text = self.state.input_buffer[:width - 4]
        try:
            write(style(text, color="white"))
        except:
            pass
    
    def _draw_status_bar(self, width: int):
        """Draw status bar"""
        y = self.height
        move_cursor(1, y)
        erase_line()
        
        parts = [
            style("✦", color="cyan"),
            style(os.path.basename(self.context.cwd), color="yellow"),
            style(f"[{self.context.backend}]", color="gray"),
        ]
        
        if self._loading:
            parts.append(style("◌ thinking", color="cyan", blink=True))
        
        if self._show_sidebar:
            parts.append(style(f"[{self._sidebar_panel.value.upper()}]", color="magenta"))
        
        try:
            status = " ".join(parts)
            write(status.ljust(width))
        except:
            pass
    
    def _render_sidebar(self):
        """Render sidebar"""
        x = self.width - self.sidebar_width + 1
        
        for y in range(1, self.height):
            move_cursor(x, y)
            try:
                write(style("│", color="gray", dim=True))
            except:
                pass
        
        if self._sidebar_panel == SidebarPanel.SESSION:
            self._render_session_panel(x)
        elif self._sidebar_panel == SidebarPanel.TOOLS:
            self._render_tools_panel(x)
        elif self._sidebar_panel == SidebarPanel.FILES:
            self._render_files_panel(x)
        elif self._sidebar_panel == SidebarPanel.GIT:
            self._render_git_panel(x)
        elif self._sidebar_panel == SidebarPanel.AGENTS:
            self._render_agents_panel(x)
    
    def _render_session_panel(self, x: int):
        """Session panel"""
        y = 2
        
        move_cursor(x, y)
        try:
            write(style(" ╭─ Session ────╮ ", color="cyan", bold=True))
        except:
            pass
        
        y += 2
        move_cursor(x, y)
        try:
            write(style(f" cwd: ", color="gray", dim=True) + os.path.basename(self.context.cwd))
        except:
            pass
        
        y += 1
        move_cursor(x, y)
        try:
            write(style(f" backend: ", color="gray", dim=True) + style(self.context.backend, color="cyan"))
        except:
            pass
        
        y += 1
        move_cursor(x, y)
        try:
            write(style(f" model: ", color="gray", dim=True) + style(self.context.model[:15], color="yellow"))
        except:
            pass
        
        y += 2
        move_cursor(x, y)
        try:
            write(style(" ╰─ Shortcuts ──╯ ", color="cyan", bold=True))
        except:
            pass
        
        shortcuts = [
            ("Ctrl+G", "Sidebar"),
            ("Ctrl+S", "Panel"),
            ("Ctrl+L", "Clear"),
            ("↑/↓", "History"),
        ]
        
        y += 1
        for key, desc in shortcuts:
            move_cursor(x, y)
            try:
                write(style(f" {key:<8}", color="magenta") + f" {desc}")
            except:
                pass
            y += 1
    
    def _render_tools_panel(self, x: int):
        """Tools panel"""
        y = 2
        
        move_cursor(x, y)
        try:
            write(style(" ╭─ Tools ──────╮ ", color="cyan", bold=True))
        except:
            pass
        
        y += 2
        
        try:
            from services.tools import get_executor
            executor = get_executor()
            tools = sorted(executor.list_tools())[:18]
        except:
            tools = []
        
        for tool in tools:
            move_cursor(x, y)
            try:
                write(f" {tool[:self.sidebar_width - 4]}")
            except:
                pass
            y += 1
    
    def _render_files_panel(self, x: int):
        """Files panel"""
        y = 2
        
        move_cursor(x, y)
        try:
            write(style(" ╭─ Files ───────╮ ", color="cyan", bold=True))
        except:
            pass
        
        y += 1
        
        try:
            entries = sorted(os.listdir(self.context.cwd), key=lambda x: (not os.path.isdir(os.path.join(self.context.cwd, x)), x))[:15]
            for entry in entries:
                if entry.startswith('.'):
                    continue
                path = os.path.join(self.context.cwd, entry)
                icon = "📁" if os.path.isdir(path) else "📄"
                move_cursor(x, y)
                try:
                    write(f" {icon} {entry[:self.sidebar_width - 5]}")
                except:
                    pass
                y += 1
        except:
            pass
    
    def _render_git_panel(self, x: int):
        """Git panel"""
        y = 2
        
        move_cursor(x, y)
        try:
            write(style(" ╭─ Git ─────────╮ ", color="cyan", bold=True))
        except:
            pass
        
        y += 2
        
        status = git_status(self.context.cwd)
        
        if not status["is_repo"]:
            move_cursor(x, y)
            try:
                write(style(" Not a git repo ", color="gray", dim=True))
            except:
                return
        
        move_cursor(x, y)
        try:
            write(style(f" branch: ", color="gray", dim=True) + style(status["branch"], color="cyan"))
        except:
            pass
        y += 1
        
        if status["staged"]:
            move_cursor(x, y)
            try:
                write(style(f" staged: ", color="gray", dim=True) + style(f"{len(status['staged'])}", color="green"))
            except:
                pass
            y += 1
        
        if status["changes"]:
            move_cursor(x, y)
            try:
                write(style(f" changed: ", color="gray", dim=True) + style(f"{len(status['changes'])}", color="yellow"))
            except:
                pass
    
    def _render_agents_panel(self, x: int):
        """Agents panel"""
        y = 2
        
        move_cursor(x, y)
        try:
            write(style(" ╭─ Agents ──────╮ ", color="cyan", bold=True))
        except:
            pass
        
        y += 2
        
        from services.agents import list_agents
        agents = list_agents()
        
        for name in list(agents.keys())[:15]:
            move_cursor(x, y)
            try:
                write(f" ◆ {name}")
            except:
                pass
            y += 1
    
    def _exit_animated(self):
        """Animated exit"""
        clear_screen()
        
        cat = CatAnimation.render(3)
        lines = [
            cat,
            "",
            style("   Thanks for using ", color="gray", dim=True) + style("Galaxy Destroyer", color="cyan", bold=True) + style("!", color="gray", dim=True),
            "",
            style("   See you next time! ", color="gray", dim=True),
            "",
        ]
        
        for line in lines:
            try:
                print(line)
            except:
                pass
            time.sleep(0.1)
    
    def _show_error(self, error: str):
        """Show error"""
        clear_screen()
        try:
            print("")
            print(style(f"   Error: {error}", color="red", bold=True))
            print("")
        except:
            print("Error occurred")
    
    def _cleanup(self):
        """Cleanup"""
        self._show_cursor()


if __name__ == "__main__":
    tui = BeautifulTUI()
    tui.run()


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: float = 0
    tool_use: Optional[Dict] = None
    expanded: bool = False


@dataclass
class ToolUse:
    name: str
    input_data: Dict
    status: str = "running"
    result: Optional[str] = None
    start_time: float = 0


class SidebarPanel(Enum):
    SESSION = "session"
    TOOLS = "tools"
    FILES = "files"
    GIT = "git"
    AGENTS = "agents"


class Transition:
    """Animation transitions"""
    
    @staticmethod
    def fade_in(text: str, speed: float = 0.01) -> None:
        for i in range(0, 256, 10):
            code = f"\033[38;2;{i},{i},{i}m"
            sys.stdout.write(code + text + "\033[0m\r")
            sys.stdout.flush()
            time.sleep(speed)
    
    @staticmethod
    def slide_in_from_right(text: str, delay: float = 0.01) -> None:
        width = get_terminal_size()[0]
        for i in range(len(text) + 1):
            spaces = " " * (width - min(i, width))
            sys.stdout.write("\r" + spaces + text[:i])
            sys.stdout.flush()
            time.sleep(delay)
    
    @staticmethod
    def typewriter(text: str, delay: float = 0.015) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)


class CatAnimation:
    """Animated cat ASCII art"""
    
    FRAMES = [
        """
      /\\_/\\  
     ( o.o ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( -.- ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( ^.^ ) 
     (")_(") 
""",
        """
      /\\_/\\  
     ( *. ) 
     (")_(") 
""",
    ]
    
    @staticmethod
    def render(frame: int = 0) -> str:
        return CatAnimation.FRAMES[frame % len(CatAnimation.FRAMES)]


class BeautifulTUI:
    """Beautiful Claude Code-like terminal UI with animations"""
    
    def __init__(self):
        self.context = Context()
        self.state = State()
        self.messages: List[ChatMessage] = []
        self.running = False
        self.width, self.height = get_terminal_size()
        self.sidebar_width = 28
        self._needs_render = True
        self._loading = False
        self._loading_text = ""
        self._loading_frame = 0
        self._tool_uses: List[ToolUse] = []
        self._show_sidebar = True
        self._sidebar_panel = SidebarPanel.SESSION
        self._thinking = False
        self._thinking_frames = ["   ", "  .", " ..", "..."]
        self._thinking_idx = 0
        self._last_think_update = 0
        self._cat_frame = 0
        self._last_cat_update = 0
        self._search_mode = False
        self._search_query = ""
        self._selected_message = -1
        self._animations_enabled = True
        
        self._setup_input()
    
    def _setup_input(self):
        """Setup input handling"""
        try:
            import tty
            import termios
            self._old_settings = termios.tcgetattr(sys.stdin)
            self._has_tty = True
        except:
            self._has_tty = False
    
    def run(self):
        """Main run loop"""
        self.running = True
        self.width, self.height = get_terminal_size()
        self._ensure_minimum_size()
        
        try:
            self._setup()
            self._show_welcome_animated()
            self._main_loop()
        except KeyboardInterrupt:
            self._exit_animated()
        except Exception as e:
            self._show_error(str(e))
        finally:
            self._cleanup()
    
    def _ensure_minimum_size(self):
        """Ensure minimum terminal size"""
        if self.width < 80:
            self.width = 80
        if self.height < 20:
            self.height = 20
    
    def _setup(self):
        """Setup terminal"""
        if os.name == 'nt':
            try:
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            except:
                pass
        
        self.context.cwd = os.getcwd()
        self._hide_cursor()
    
    def _hide_cursor(self):
        """Hide cursor"""
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
    
    def _show_cursor(self):
        """Show cursor"""
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    
    def _show_welcome_animated(self):
        """Show animated welcome"""
        clear_screen()
        
        cat_frame = CatAnimation.render(0)
        
        lines = [
            style(cat_frame, color="cyan"),
            "",
            style(" ╔══════════════════════════════════════════════════════════════╗", color="cyan", bold=True),
            style(" ║", color="cyan") + style("     ★  GALAXY DESTROYER  ★                              ", color="white", bold=True, bg_color="blue").ljust(62) + style("║", color="cyan"),
            style(" ║", color="cyan") + style("       AI-Powered Terminal Assistant                      ", color="gray", dim=True).ljust(62) + style("║", color="cyan"),
            style(" ╚══════════════════════════════════════════════════════════════╝", color="cyan", bold=True),
            "",
            style("  Getting Started:", color="yellow", bold=True),
            "",
            style("    ask <msg>", color="green") + "    - Chat with AI",
            style("    agents", color="green") + "      - List agents",
            style("    tools", color="green") + "       - List tools",
            style("    run <cmd>", color="green") + "    - Execute shell",
            style("    task", color="green") + "        - Task management",
            "",
            style("  Keyboard Shortcuts:", color="yellow", bold=True),
            "",
            style("    Ctrl+G", color="magenta") + " - Toggle sidebar",
            style("    Ctrl+S", color="magenta") + " - Cycle panels",
            style("    Ctrl+L", color="magenta") + " - Clear screen",
            style("    Ctrl+R", color="magenta") + " - Search",
            style("    ↑/↓", color="magenta") + "    - History",
            style("    Tab", color="magenta") + "      - Autocomplete",
            "",
            style("  Default: OpenCode.ai backend (no API key needed!)", color="gray", dim=True),
            "",
        ]
        
        for line in lines:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            time.sleep(0.02)
        
        time.sleep(0.5)
    
    def _main_loop(self):
        """Main loop"""
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            
            if self._needs_render:
                self._render()
                self._needs_render = False
            
            if self._loading and current_time - last_time > 0.1:
                self._loading_frame = (self._loading_frame + 1) % 8
                last_time = current_time
                self._render_loading()
            
            if self._thinking and current_time - self._last_think_update > 0.3:
                self._thinking_idx = (self._thinking_idx + 1) % 4
                self._last_think_update = current_time
                self._render_status_bar()
            
            key = self._read_key()
            
            if key:
                self._handle_key(key)
                self._needs_render = True
            else:
                time.sleep(0.02)
    
    def _read_key(self) -> Optional[str]:
        """Read key without blocking"""
        if not self._has_tty:
            return None
        
        try:
            import tty
            import termios
            
            if sys.platform == 'win32':
                import msvcrt
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\r':
                        return "enter"
                    elif char == b'\x08':
                        return "backspace"
                    elif char == b'\x1b':
                        return "escape"
                    return char.decode('utf-8', errors='ignore')
            else:
                import select
                if select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char == '\n':
                        return "enter"
                    elif char == '\t':
                        return "tab"
                    elif char == '\x7f':
                        return "backspace"
                    elif char == '\x03':
                        return "ctrl_c"
                    return char
        except:
            pass
        
        return None
    
    def _render_loading(self):
        """Render loading spinner"""
        spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        spin = spinners[self._loading_frame]
        
        content_width = self.width - self.sidebar_width - 2
        
        pos_y = self.height - 1
        pos_x = 1
        
        move_cursor(pos_x, pos_y)
        erase_line()
        
        text = f" {spin} {self._loading_text}"
        write(style(text, color="cyan", bold=True))
    
    def _handle_key(self, key: str):
        """Handle key press"""
        if key == "ctrl_c":
            if self.state.input_buffer:
                self.state.input_buffer = ""
                self._render_input_line()
            else:
                self.running = False
            return
        
        if key == "escape":
            self._search_mode = False
            return
        
        if key == "ctrl_l":
            clear_screen()
            self._render()
            return
        
        if key == "ctrl_g":
            self._show_sidebar = not self._show_sidebar
            return
        
        if key == "ctrl_s":
            self._cycle_sidebar()
            return
        
        if key == "enter":
            self._execute_input()
            return
        
        if key == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
                self._render_input_line()
            return
        
        if key in ["up", "down"]:
            if key == "up":
                self._history_prev()
            else:
                self._history_next()
            return
        
        if len(key) == 1:
            self.state.input_buffer += key
            self._render_input_line()
    
    def _cycle_sidebar(self):
        """Cycle sidebar panel"""
        panels = list(SidebarPanel)
        idx = panels.index(self._sidebar_panel)
        self._sidebar_panel = panels[(idx + 1) % len(panels)]
    
    def _history_prev(self):
        """Previous history"""
        if self.state.history and self.state.history_index < len(self.state.history) - 1:
            self.state.history_index += 1
            idx = len(self.state.history) - 1 - self.state.history_index
            if idx >= 0:
                self.state.input_buffer = self.state.history[idx]
                self._render_input_line()
    
    def _history_next(self):
        """Next history"""
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
    
    def _execute_input(self):
        """Execute input"""
        cmd = self.state.input_buffer.strip()
        
        if not cmd:
            write_line("")
            self._draw_input_prompt(self.width - self.sidebar_width - 2 if self._show_sidebar else self.width)
            return
        
        self.state.add_to_history(cmd)
        self.state.input_buffer = ""
        
        self._add_message("user", cmd)
        self._process_command(cmd)
    
    def _process_command(self, cmd: str):
        """Process command"""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ("ask", "ai"):
            self._handle_ai(args)
        elif command == "help":
            self._show_help()
        elif command == "clear":
            self.messages.clear()
            clear_screen()
            self._render()
        elif command in ("exit", "quit"):
            self.running = False
        elif command == "status":
            self._show_status()
        elif command == "tools":
            self._list_tools()
        elif command == "agents":
            self._list_agents()
        elif command == "run":
            self._run_shell(args)
        elif command == "tasks":
            self._list_tasks()
        else:
            self._handle_ai(cmd)
    
    def _handle_ai(self, prompt: str):
        """Handle AI"""
        if not prompt:
            self._add_message("system", "Usage: ask <message>")
            return
        
        self._loading = True
        self._loading_text = "Thinking"
        
        thread = threading.Thread(target=self._async_ai, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _async_ai(self, prompt: str):
        """Async AI call"""
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
        
        backend = Backend.OPENCODE
        api_key = os.environ.get("OPENCODE_API_KEY", "")
        
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
                self._complete_tool(tool_use.name, result.content if result.content else result.error)
                return result
            except Exception as e:
                self._complete_tool(tool_use.name, str(e), error=True)
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
        tool = ToolUse(name=name, input_data=input_data, start_time=time.time())
        self._tool_uses.append(tool)
        self._render_messages()
    
    def _complete_tool(self, name: str, result: str, error: bool = False):
        """Complete tool"""
        for tool in self._tool_uses:
            if tool.name == name and tool.status == "running":
                tool.status = "completed" if not error else "error"
                tool.result = result
                break
        self._render_messages()
    
    def _show_help(self):
        """Show help"""
        self._add_message("system", """
╔══════════════════════════════════════════════════════════════╗
║                    Galaxy Destroyer Commands                  ║
╚══════════════════════════════════════════════════════════════╝

AI & Chat:
  ask <msg>      - Chat with AI
  agents        - List available agents

Tools & Shell:
  tools         - List all tools
  tool <name>   - Run a specific tool
  run <cmd>     - Execute shell command
  !<cmd>        - Execute shell (shortcut)

Tasks:
  task list     - List all tasks
  task create   - Create new task
  task update   - Update task status

Session:
  status        - Show current status
  clear         - Clear conversation
  help          - Show this help
  exit          - Exit

Keyboard Shortcuts:
  Ctrl+G - Toggle sidebar    Ctrl+S - Cycle sidebar
  Ctrl+L - Clear screen      Ctrl+R - Search
  ↑/↓   - Command history    Tab    - Autocomplete
""")
    
    def _show_status(self):
        """Show status"""
        status = f"""
╔══════════════════════════════════════════════════════════════╗
║                       Status Information                      ║
╚══════════════════════════════════════════════════════════════╝

  Backend:  {self.context.backend}
  Model:    {self.context.model}
  CWD:      {self.context.cwd}
  Messages: {len(self.messages)}
  Tools:    {len(self._tool_uses)}
"""
        self._add_message("system", status)
    
    def _list_tools(self):
        """List tools"""
        from services.tools import get_executor
        executor = get_executor()
        tools = sorted(executor.list_tools())
        
        msg = "╔══════════════════════════════════════════════════════════════╗\n"
        msg += "║                       Available Tools                          ║\n"
        msg += "╚══════════════════════════════════════════════════════════════╝\n"
        
        for tool in tools[:30]:
            msg += f"  {tool}\n"
        
        self._add_message("system", msg)
    
    def _list_agents(self):
        """List agents"""
        from services.agents import list_agents
        agents = list_agents()
        
        msg = "╔══════════════════════════════════════════════════════════════╗\n"
        msg += "║                       Available Agents                         ║\n"
        msg += "╚══════════════════════════════════════════════════════════════╝\n"
        
        for name, desc in agents.items():
            msg += f"  {name}: {desc[:60]}...\n"
        
        self._add_message("system", msg)
    
    def _list_tasks(self):
        """List tasks"""
        from services.tasks import task_list
        result = task_list()
        
        msg = f"Tasks ({result.get('count', 0)}):\n"
        
        for task in result.get('tasks', [])[:10]:
            status = "○" if task['status'] == 'pending' else "◉" if task['status'] == 'in_progress' else "✓"
            msg += f"  {status} {task.get('title', 'Untitled')}\n"
        
        self._add_message("system", msg)
    
    def _run_shell(self, cmd: str):
        """Run shell"""
        if not cmd:
            return
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr or "(no output)"
            self._add_message("system", f"$ {cmd}\n{output[:500]}")
        except Exception as e:
            self._add_message("error", f"Error: {str(e)}")
    
    def _render(self):
        """Render full UI"""
        clear_screen()
        
        content_width = self.width - self.sidebar_width - 2 if self._show_sidebar else self.width
        
        self._draw_header(content_width)
        self._render_messages(content_width)
        self._draw_input_prompt(content_width)
        self._draw_status_bar(content_width)
        
        if self._show_sidebar:
            self._render_sidebar()
        
        self._render_input_line()
    
    def _render_messages(self, width: int):
        """Render messages"""
        start = 3
        
        move_cursor(1, start)
        
        for msg in self.messages[-15:]:
            if msg.role == "user":
                write_line(style("  ✦ You ", color="green", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="white"))
            elif msg.role == "assistant":
                write_line(style("  ✦ Galaxy ", color="cyan", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="gray"))
            elif msg.role == "error":
                write_line(style("  ✦ Error ", color="red", bold=True))
                for line in word_wrap(msg.content, width - 4):
                    write_line(style(f"    {line}", color="red"))
            else:
                for line in word_wrap(msg.content, width - 2):
                    write_line(style(line, color="gray", dim=True))
        
        for tool in self._tool_uses[-5:]:
            status_color = "green" if tool.status == "completed" else "yellow"
            icon = "✓" if tool.status == "completed" else "◉"
            write_line(style(f"  {icon} {tool.name}", color=status_color, bold=True))
    
    def _draw_header(self, width: int):
        """Draw header"""
        move_cursor(1, 1)
        
        header = style(" ✦ GALAXY DESTROYER ", bg_color="blue", color="white", bold=True)
        write(header.ljust(width))
        
        move_cursor(1, 2)
        write(style("─" * width, color="gray"))
    
    def _draw_input_prompt(self, width: int):
        """Draw input prompt"""
        y = self.height - 1
        move_cursor(1, y)
        erase_line()
        
        prompt = style(" ✦ ", color="cyan", bold=True)
        write(prompt)
    
    def _render_input_line(self):
        """Render input line"""
        width = self.width - self.sidebar_width - 2 if self._show_sidebar else self.width
        
        y = self.height - 1
        move_cursor(3, y)
        erase_line()
        
        text = self.state.input_buffer[:width - 4]
        write(style(text, color="white"))
    
    def _draw_status_bar(self, width: int):
        """Draw status bar"""
        y = self.height
        move_cursor(1, y)
        erase_line()
        
        parts = [
            style("✦", color="cyan"),
            style(os.path.basename(self.context.cwd), color="yellow"),
            style(f"[{self.context.backend}]", color="gray"),
        ]
        
        if self._loading:
            parts.append(style("◌ thinking", color="cyan", blink=True))
        
        if self._show_sidebar:
            parts.append(style(f"[{self._sidebar_panel.value.upper()}]", color="magenta"))
        
        status = " ".join(parts)
        write(status.ljust(width))
    
    def _render_sidebar(self):
        """Render sidebar"""
        x = self.width - self.sidebar_width + 1
        
        for y in range(1, self.height):
            move_cursor(x, y)
            write(style("│", color="gray", dim=True))
        
        if self._sidebar_panel == SidebarPanel.SESSION:
            self._render_session_panel(x)
        elif self._sidebar_panel == SidebarPanel.TOOLS:
            self._render_tools_panel(x)
        elif self._sidebar_panel == SidebarPanel.FILES:
            self._render_files_panel(x)
        elif self._sidebar_panel == SidebarPanel.GIT:
            self._render_git_panel(x)
        elif self._sidebar_panel == SidebarPanel.AGENTS:
            self._render_agents_panel(x)
    
    def _render_session_panel(self, x: int):
        """Session panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" ╭─ Session ────╮ ", color="cyan", bold=True))
        
        y += 2
        move_cursor(x, y)
        write(style(f" cwd: ", color="gray", dim=True) + os.path.basename(self.context.cwd))
        
        y += 1
        move_cursor(x, y)
        write(style(f" backend: ", color="gray", dim=True) + style(self.context.backend, color="cyan"))
        
        y += 1
        move_cursor(x, y)
        write(style(f" model: ", color="gray", dim=True) + style(self.context.model[:15], color="yellow"))
        
        y += 2
        move_cursor(x, y)
        write(style(" ╰─ Shortcuts ──╯ ", color="cyan", bold=True))
        
        shortcuts = [
            ("Ctrl+G", "Sidebar"),
            ("Ctrl+S", "Panel"),
            ("Ctrl+L", "Clear"),
            ("↑/↓", "History"),
        ]
        
        y += 1
        for key, desc in shortcuts:
            move_cursor(x, y)
            write(style(f" {key:<8}", color="magenta") + f" {desc}")
            y += 1
    
    def _render_tools_panel(self, x: int):
        """Tools panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" ╭─ Tools ──────╮ ", color="cyan", bold=True))
        
        y += 2
        
        try:
            from services.tools import get_executor
            executor = get_executor()
            tools = sorted(executor.list_tools())[:18]
        except:
            tools = []
        
        for tool in tools:
            move_cursor(x, y)
            write(f" {tool[:self.sidebar_width - 4]}")
            y += 1
    
    def _render_files_panel(self, x: int):
        """Files panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" ╭─ Files ───────╮ ", color="cyan", bold=True))
        
        y += 1
        
        try:
            entries = sorted(os.listdir(self.context.cwd), key=lambda x: (not os.path.isdir(os.path.join(self.context.cwd, x)), x))[:15]
            for entry in entries:
                if entry.startswith('.'):
                    continue
                path = os.path.join(self.context.cwd, entry)
                icon = "📁" if os.path.isdir(path) else "📄"
                move_cursor(x, y)
                write(f" {icon} {entry[:self.sidebar_width - 5]}")
                y += 1
        except:
            pass
    
    def _render_git_panel(self, x: int):
        """Git panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" ╭─ Git ─────────╮ ", color="cyan", bold=True))
        
        y += 2
        
        status = git_status(self.context.cwd)
        
        if not status["is_repo"]:
            move_cursor(x, y)
            write(style(" Not a git repo ", color="gray", dim=True))
            return
        
        move_cursor(x, y)
        write(style(f" branch: ", color="gray", dim=True) + style(status["branch"], color="cyan"))
        y += 1
        
        if status["staged"]:
            move_cursor(x, y)
            write(style(f" staged: ", color="gray", dim=True) + style(f"{len(status['staged'])}", color="green"))
            y += 1
        
        if status["changes"]:
            move_cursor(x, y)
            write(style(f" changed: ", color="gray", dim=True) + style(f"{len(status['changes'])}", color="yellow"))
            y += 1
    
    def _render_agents_panel(self, x: int):
        """Agents panel"""
        y = 2
        
        move_cursor(x, y)
        write(style(" ╭─ Agents ──────╮ ", color="cyan", bold=True))
        
        y += 2
        
        from services.agents import list_agents
        agents = list_agents()
        
        for name in list(agents.keys())[:15]:
            move_cursor(x, y)
            write(f" ◆ {name}")
            y += 1
    
    def _exit_animated(self):
        """Animated exit"""
        clear_screen()
        
        cat = CatAnimation.render(3)
        lines = [
            cat,
            "",
            style("   Thanks for using ", color="gray", dim=True) + style("Galaxy Destroyer", color="cyan", bold=True) + style("!", color="gray", dim=True),
            "",
            style("   See you next time! ", color="gray", dim=True),
            "",
        ]
        
        for line in lines:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            time.sleep(0.1)
    
    def _show_error(self, error: str):
        """Show error"""
        clear_screen()
        write_line("")
        write_line(style(f"   Error: {error}", color="red", bold=True))
        write_line("")
    
    def _cleanup(self):
        """Cleanup"""
        self._show_cursor()


class Context:
    """Simple context"""
    cwd = ""
    backend = "opencode"
    model = "qwen2.5-coder"


class State:
    """Simple state"""
    input_buffer = ""
    history = []
    history_index = -1


if __name__ == "__main__":
    tui = BeautifulTUI()
    tui.run()