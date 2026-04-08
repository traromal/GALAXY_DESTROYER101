"""Test script to verify Galaxy Destroyer works"""

import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

import core.app
import commands
import commands.builtin
import commands.git
import tools.registry
import tools.builtin
import services.tools.executor
import services.tools.builtin as svc_tools
import state.store
import utils.helpers
import utils.vim


def test_core():
    print("Testing core modules...")
    
    from core.state import Context, State
    from core.render import style, get_terminal_size
    
    ctx = Context()
    print(f"  Context: cwd={ctx.cwd}")
    
    state = State()
    print(f"  State: mode={state.mode}")
    
    print(f"  Terminal: {get_terminal_size()}")
    
    print(style("  Style test", bold=True, color="green"))
    print("  Core OK!")


def test_commands():
    print("\nTesting commands...")
    
    registry = commands.get_commands()
    cmds = registry.list_all()
    print(f"  Registered commands: {len(cmds)}")
    for cmd in cmds[:10]:
        print(f"    - {cmd.name}: {cmd.description}")
    print("  Commands OK!")


def test_tools():
    print("\nTesting tools...")
    
    executor = services.tools.executor.get_executor()
    tools_list = executor.list_tools()
    print(f"  Registered tools: {len(tools_list)}")
    for tool in tools_list[:10]:
        print(f"    - {tool}")
    print("  Tools OK!")


def test_execution():
    print("\nTesting command execution...")
    
    result = commands.execute_command("pwd", [], app=None)
    print(f"  pwd: {result}")
    
    result = commands.execute_command("date", [], app=None)
    print(f"  date: {result}")
    
    result = commands.execute_command("whoami", [], app=None)
    print(f"  whoami: {result}")
    
    result = commands.execute_command("git", ["status"], app=None)
    print(f"  git status: {result[:50]}..." if len(result) > 50 else f"  git status: {result}")
    
    print("  Execution OK!")


def test_state():
    print("\nTesting state...")
    
    from state.store import AppState, Store, get_store
    
    store = get_store()
    state = store.get_state()
    print(f"  State mode: {state.mode}")
    print(f"  State cwd: {state.cwd}")
    print("  State OK!")


def test_utils():
    print("\nTesting utils...")
    
    from utils.helpers import get_platform, is_windows, timestamp, format_size
    
    print(f"  Platform: {get_platform()}")
    print(f"  Windows: {is_windows()}")
    print(f"  Time: {timestamp()}")
    print(f"  Size: {format_size(1024)}")
    print("  Utils OK!")


def test_vim():
    print("\nTesting vim editor...")
    
    from utils.vim import VimEditor, VimMode
    
    vim = VimEditor()
    print(f"  Mode: {vim.get_mode()}")
    buffer, cursor = vim.handle_key('i', "hello", 2)
    print(f"  After 'i': buffer='{buffer}', cursor={cursor}")
    buffer, cursor = vim.handle_key('Escape', buffer, cursor)
    print(f"  After Escape: mode={vim.get_mode()}")
    print("  Vim OK!")


if __name__ == "__main__":
    print("=" * 50)
    print(" Galaxy Destroyer Test Suite")
    print("=" * 50)
    
    try:
        test_core()
        test_commands()
        test_tools()
        test_execution()
        test_state()
        test_utils()
        test_vim()
        
        print("\n" + "=" * 50)
        print(" ALL TESTS PASSED!")
        print("=" * 50)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)