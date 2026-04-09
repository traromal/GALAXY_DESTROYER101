"""Core application module - handles the main loop and input"""

import os
import sys
import select
import time
from typing import Optional, Callable
from dataclasses import dataclass

from .state import Context, State, Color
from .render import (
    get_terminal_size,
    clear_screen,
    move_cursor,
    write,
    write_line,
    style,
    BorderStyle,
    DOUBLE_BORDER,
    word_wrap,
)


@dataclass
class Key:
    """Represents a key press"""

    name: str
    value: str
    ctrl: bool = False
    meta: bool = False
    shift: bool = False


class InputHandler:
    """Handles keyboard input"""

    ESCAPE_SEQUENCES = {
        "\x1b[A": "up",
        "\x1b[B": "down",
        "\x1b[C": "right",
        "\x1b[D": "left",
        "\x1b[H": "home",
        "\x1b[F": "end",
        "\x1b[3~": "delete",
        "\x1b[2~": "insert",
        "\x1b[5~": "pageup",
        "\x1b[6": "pagedown",
        "\x1bOP": "f1",
        "\x1bOQ": "f2",
        "\x1bOR": "f3",
        "\x1bOS": "f4",
        "\x1b[15~": "f5",
        "\x1b[17~": "f6",
        "\x1b[18~": "f7",
        "\x1b[19~": "f8",
        "\x1b[20~": "f9",
        "\x1b[21~": "f10",
        "\x1b[23~": "f11",
        "\x1b[24~": "f12",
        "\r": "enter",
        "\n": "enter",
        "\t": "tab",
        "\x7f": "backspace",
        "\x03": "ctrl_c",
        "\x04": "ctrl_d",
    }

    def __init__(self):
        self.buffer = ""
        self._use_windows = os.name == "nt"

    def read_key(self) -> Optional[Key]:
        """Read a single key press"""
        if self._use_windows:
            return self._read_key_windows()
        return self._read_key_unix()

    def _read_key_windows(self) -> Optional[Key]:
        import msvcrt

        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b"\xe0":
                ch = msvcrt.getch()
                key_map = {
                    b"H": "up",
                    b"P": "down",
                    b"M": "right",
                    b"K": "left",
                    b"G": "home",
                    b"O": "end",
                    b"S": "delete",
                }
                name = key_map.get(ch, "unknown")
                return Key(name=name, value=ch.decode("utf-8", errors="replace"))
            elif ch == b"\r":
                return Key(name="enter", value="\r")
            elif ch == b"\x08":
                return Key(name="backspace", value="\x08")
            elif ch == b"\x03":
                return Key(name="ctrl_c", value="\x03", ctrl=True)
            elif ch == b"\x1b":
                return Key(name="escape", value="\x1b", meta=True)
            else:
                try:
                    char = ch.decode("utf-8")
                    return Key(name=char, value=char)
                except:
                    return None
        return None

    def _read_key_unix(self) -> Optional[Key]:
        try:
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)

                if char == "\x1b":
                    seq = char
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq += sys.stdin.read(1)
                        if seq == "\x1b[":
                            while select.select([sys.stdin], [], [], 0.05)[0]:
                                seq += sys.stdin.read(1)

                    name = self.ESCAPE_SEQUENCES.get(seq, seq)
                    return Key(name=name, value=seq, meta=True)

                elif char in self.ESCAPE_SEQUENCES:
                    name = self.ESCAPE_SEQUENCES[char]
                    ctrl = (
                        char
                        in "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
                    )
                    return Key(name=name, value=char, ctrl=ctrl)

                return Key(name=char, value=char)
        except:
            pass
        return None


class GalaxyApp:
    """Main application class - the heart of the TUI"""

    def __init__(self):
        self.context = Context()
        self.state = State()
        self.input_handler = InputHandler()
        self.running = False
        self._callbacks = {}
        self._components = []
        self._needs_render = True
        self._render_lock = False

    def on(self, event: str, callback: Callable):
        """Register event callback"""
        self._callbacks[event] = callback

    def emit(self, event: str, *args, **kwargs):
        """Emit event to callbacks"""
        if event in self._callbacks:
            self._callbacks[event](*args, **kwargs)

    def register_component(self, component):
        """Register a UI component"""
        self._components.append(component)

    def run(self):
        """Main application loop"""
        self.running = True

        try:
            self._setup()
            self._main_loop()
        except KeyboardInterrupt:
            write_line("\n" + style("Interrupted", color="yellow"))
        finally:
            self._cleanup()

    def _setup(self):
        """Initialize the application"""
        if os.name == "nt":
            import msvcrt

            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        else:
            os.system("stty -echo -icanon 2>/dev/null || true")
        self.context.cwd = os.getcwd()
        self.context.session_id = str(int(time.time()))
        self.emit("init")

    def _main_loop(self):
        """Main event loop"""
        while self.running:
            if self._needs_render and not self._render_lock:
                self._render_lock = True
                self.render()
                self._needs_render = False
                self._render_lock = False

            key = self.input_handler.read_key()

            if key:
                self.handle_key(key)
                self._needs_render = True
            else:
                time.sleep(0.01)

    def handle_key(self, key: Key):
        """Handle key press"""
        if key.name == "ctrl_c":
            self.running = False
            return

        if key.name == "enter":
            self._execute_input()
            self._needs_render = True
            return

        if key.name == "backspace":
            if self.state.input_buffer:
                self.state.input_buffer = self.state.input_buffer[:-1]
            self._needs_render = True
            return

        if key.name == "up":
            self._history_previous()
            self._needs_render = True
            return

        if key.name == "down":
            self._history_next()
            self._needs_render = True
            return

        if key.name == "left":
            if self.state.cursor_pos > 0:
                self.state.cursor_pos -= 1
            self._needs_render = True
            return

        if key.name == "right":
            if self.state.cursor_pos < len(self.state.input_buffer):
                self.state.cursor_pos += 1
            self._needs_render = True
            return

        if key.name == "ctrl_a":
            self.state.cursor_pos = 0
            self._needs_render = True
            return

        if key.name == "ctrl_e":
            self.state.cursor_pos = len(self.state.input_buffer)
            self._needs_render = True
            return

        if key.name == "ctrl_u":
            self.state.input_buffer = ""
            self.state.cursor_pos = 0
            self._needs_render = True
            return

        if key.name == "ctrl_k":
            self.state.input_buffer = self.state.input_buffer[: self.state.cursor_pos]
            self._needs_render = True
            return

        if key.name == "tab":
            self._complete()
            self._needs_render = True
            return

        if key.name == "escape":
            self.state.input_buffer = ""
            self.state.cursor_pos = 0
            self._needs_render = True
            return

        if len(key.value) == 1 and not key.meta:
            self.state.input_buffer += key.value
            self.state.cursor_pos += 1
            self._needs_render = True

    def _execute_input(self):
        """Execute the current input"""
        cmd = self.state.input_buffer.strip()

        if not cmd:
            self.state.push_output("")
            self.state.input_buffer = ""
            self.state.cursor_pos = 0
            return

        self.state.add_to_history(cmd)
        self.state.push_output(f"> {cmd}")

        self.emit("command", cmd)

        self.state.input_buffer = ""
        self.state.cursor_pos = 0

    def _history_previous(self):
        """Go to previous command in history"""
        if self.state.history and self.state.history_index > 0:
            self.state.history_index -= 1
            self.state.input_buffer = self.state.history[self.state.history_index]
            self.state.cursor_pos = len(self.state.input_buffer)

    def _history_next(self):
        """Go to next command in history"""
        if self.state.history_index < len(self.state.history) - 1:
            self.state.history_index += 1
            self.state.input_buffer = self.state.history[self.state.history_index]
            self.state.cursor_pos = len(self.state.input_buffer)
        elif self.state.history_index == len(self.state.history) - 1:
            self.state.input_buffer = ""
            self.state.cursor_pos = 0
            self.state.history_index += 1

    def _complete(self):
        """Handle tab completion"""
        self.emit("complete", self.state.input_buffer)

    def render(self):
        """Render the UI"""
        width, height = get_terminal_size()

        clear_screen()

        self._render_header(width)
        self._render_output(width, height)
        self._render_input(width)
        self._render_status(width)

        move_cursor(1, height)

    def _render_header(self, width: int):
        """Render the header bar"""
        title = " Galaxy Destroyer "
        header = style(title, bold=True, color="cyan")
        info = f" {self.context.model} | {self.context.cwd} "

        padding = width - len(title) - len(info)
        line = header + " " * padding + info
        write_line(line)
        write_line(style("─" * width, color="gray"))

    def _render_output(self, width: int, height: int):
        """Render output area"""
        output_height = height - 5

        for i, line in enumerate(self.state.output_buffer[-output_height:]):
            if len(line) > width:
                line = line[: width - 3] + "..."
            write_line(line)

        if len(self.state.output_buffer) > output_height:
            write_line(
                style(
                    f"  ↑ {len(self.state.output_buffer) - output_height} more lines",
                    color="gray",
                )
            )

    def _render_input(self, width: int):
        """Render input line"""
        write_line(style("─" * width, color="gray"))

        prompt = style(">>> ", color="green", bold=True)

        if self.state.is_loading:
            prompt = style(">>> ", color="yellow", bold=True)

        input_display = self.state.input_buffer

        write(prompt + input_display)

        if self.state.cursor_pos < len(self.state.input_buffer):
            move_cursor(
                len(prompt) + self.state.cursor_pos + 1, get_terminal_size()[1] - 2
            )

    def _render_status(self, width: int):
        """Render status bar"""
        write_line("")
        mode_str = f" [{self.state.mode.upper()}] "

        status_parts = [
            mode_str,
            f"msg: {len(self.context.messages)}",
            f"tools: {len(self.context.tools)}",
        ]

        if self.state.error:
            status_parts.append(style(f" ERR: {self.state.error}", color="red"))

        status = " | ".join(status_parts)
        status = status.ljust(width)

        write_line(status)

    def _cleanup(self):
        """Clean up before exit"""
        os.system("stty echo icanon 2>/dev/null" if os.name != "nt" else "")
        write_line(style("\nGoodbye!", color="cyan"))

    def set_mode(self, mode: str):
        """Set the editor mode (normal, insert, visual, command)"""
        self.state.mode = mode
        self.emit("mode_changed", mode)

    def set_error(self, error: str):
        """Set error message"""
        self.state.error = error

    def clear_error(self):
        """Clear error message"""
        self.state.error = None

    def show_loading(self, loading: bool):
        """Show/hide loading indicator"""
        self.state.is_loading = loading

    def add_output(self, text: str):
        """Add text to output"""
        for line in text.split("\n"):
            self.state.push_output(line)
        self._needs_render = True

    def mark_dirty(self):
        """Mark UI as needing render"""
        self._needs_render = True

    async def build_system_context(self) -> dict:
        """Build system context including git status and memory"""
        from .context import get_git_context
        from .memory import build_memory_prompt

        context = {}

        git_context = await get_git_context()
        context.update(git_context)

        memory_prompt = build_memory_prompt()
        if memory_prompt:
            context["memory"] = memory_prompt

        return context
