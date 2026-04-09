"""Built-in commands"""

import os
import subprocess

from . import register_command, CommandCategory


@register_command(
    name="help",
    description="Show help information",
    category=CommandCategory.HELP,
    usage="help [command]",
    examples=["help", "help commit"],
)
def cmd_help(args=None, app=None):
    if not args:
        from galaxy_destroyer.commands import get_commands

        registry = get_commands()
        lines = ["Available Commands:", ""]

        for cat in CommandCategory:
            cmds = registry.list_by_category(cat)
            if cmds:
                lines.append(f"{cat.value.upper()}:")
                for cmd in cmds:
                    lines.append(f"  {cmd.name:15} - {cmd.description}")
                lines.append("")

        return "\n".join(lines)

    cmd_name = args[0]
    cmd = registry.get(cmd_name)
    if cmd:
        lines = [
            f"Command: {cmd.name}",
            f"Description: {cmd.description}",
            f"Category: {cmd.category.value}",
        ]
        if cmd.aliases:
            lines.append(f"Aliases: {', '.join(cmd.aliases)}")
        if cmd.usage:
            lines.append(f"Usage: {cmd.usage}")
        if cmd.examples:
            lines.append("Examples:")
            for ex in cmd.examples:
                lines.append(f"  {ex}")
        return "\n".join(lines)

    return f"Unknown command: {cmd_name}"


@register_command(
    name="clear",
    description="Clear the screen",
    category=CommandCategory.GENERAL,
    aliases=["cls"],
)
def cmd_clear(args=None, app=None):
    if app:
        app.state.clear_output()
    return ""


@register_command(
    name="exit",
    description="Exit the application",
    category=CommandCategory.GENERAL,
    aliases=["quit", "q"],
)
def cmd_exit(args=None, app=None):
    if app:
        app.running = False
    return "Goodbye!"


@register_command(
    name="status", description="Show current status", category=CommandCategory.GENERAL
)
def cmd_status(args=None, app=None):
    if not app:
        return "Status: Not in interactive mode"

    lines = [
        "=== Galaxy Destroyer Status ===",
        f"Backend: {app.context.backend}",
        f"Model: {app.context.model}",
        f"Vim Mode: {'On' if app.context.vim_mode else 'Off'}",
        f"Messages: {len(app.context.messages)}",
    ]

    if hasattr(app, "session"):
        lines.append(f"Session: {app.session.id}")
        lines.append(f"Project: {app.session.project_dir}")
        lines.append(
            f"Git: {'Yes (' + app.session.git_branch + ')' if app.session.is_git else 'No'}"
        )

    return "\n".join(lines)


@register_command(
    name="config",
    description="Show or set configuration",
    category=CommandCategory.GENERAL,
    usage="config [key [value]]",
    examples=["config", "config backend opencode", "config model llama3"],
)
def cmd_config(args=None, app=None):
    from services.config import get_config, set_config

    if not args:
        config = get_config()
        lines = ["=== Configuration ==="]
        for key, value in config.items():
            if key != "api_key":
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    key = args[0]

    if len(args) == 1:
        value = get_config(key)
        return f"{key}: {value}"

    value = args[1]
    set_config(key, value)
    return f"Set {key} = {value}"


@register_command(
    name="session",
    description="Manage session",
    category=CommandCategory.GENERAL,
    aliases=["clear-session"],
)
def cmd_session(args=None, app=None):
    if not app:
        return "Not in interactive mode"

    if hasattr(app, "session"):
        app.session = None

    app.context.clear_messages()

    if hasattr(app, "_system_prompt"):
        app._system_prompt = None

    return "Session cleared!"


@register_command(
    name="ls",
    description="List directory contents",
    category=CommandCategory.FILE,
    aliases=["dir"],
    usage="ls [path]",
    examples=["ls", "ls -la"],
)
def cmd_ls(args=None, app=None):
    path = args[0] if args else "."
    try:
        result = subprocess.run(["ls", path], capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout or "(empty)"
    except FileNotFoundError:
        return "Error: ls not found"


@register_command(
    name="cd",
    description="Change directory",
    category=CommandCategory.FILE,
    usage="cd <directory>",
)
def cmd_cd(args=None, app=None):
    if not args:
        return "Usage: cd <directory>"

    path = args[0]

    if path == "~":
        path = os.path.expanduser("~")
    elif path == "..":
        path = os.path.dirname(app.context.cwd if app else os.getcwd())

    try:
        os.chdir(path)
        if app:
            app.context.cwd = os.getcwd()
        return f"Changed to: {os.getcwd()}"
    except FileNotFoundError:
        return f"Not found: {path}"
    except PermissionError:
        return f"Permission denied: {path}"


@register_command(
    name="pwd", description="Print working directory", category=CommandCategory.FILE
)
def cmd_pwd(args=None, app=None):
    return os.getcwd()


@register_command(
    name="cat",
    description="Display file contents",
    category=CommandCategory.FILE,
    usage="cat <file>",
)
def cmd_cat(args=None, app=None):
    if not args:
        return "Usage: cat <file>"

    filepath = os.path.join(app.context.cwd if app else os.getcwd(), args[0])

    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Not found: {args[0]}"
    except PermissionError:
        return f"Denied: {args[0]}"


@register_command(
    name="echo",
    description="Print text",
    category=CommandCategory.GENERAL,
    usage="echo <text>",
)
def cmd_echo(args=None, app=None):
    if not args:
        return ""
    return os.path.expandvars(" ".join(args))


@register_command(
    name="whoami", description="Current user", category=CommandCategory.SYSTEM
)
def cmd_whoami(args=None, app=None):
    return os.environ.get("USERNAME", os.environ.get("USER", "unknown"))


@register_command(
    name="date", description="Show date/time", category=CommandCategory.SYSTEM
)
def cmd_date(args=None, app=None):
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@register_command(
    name="history", description="Show command history", category=CommandCategory.GENERAL
)
def cmd_history(args=None, app=None):
    if not app:
        return "No context"
    lines = ["Command History:", ""]
    for i, cmd in enumerate(app.state.history):
        lines.append(f"  {i + 1:3}  {cmd}")
    return "\n".join(lines)


@register_command(
    name="mode",
    description="Change editor mode",
    category=CommandCategory.GENERAL,
    usage="mode [normal|insert|visual|command]",
)
def cmd_mode(args=None, app=None):
    if not args:
        return f"Current mode: {app.state.mode}" if app else "No app"

    mode = args[0].lower()
    valid = ["normal", "insert", "visual", "command"]

    if mode not in valid:
        return f"Invalid mode. Choose: {', '.join(valid)}"

    if app:
        app.set_mode(mode)

    return f"Mode: {mode}"


@register_command(
    name="status",
    description="Show application status",
    category=CommandCategory.GENERAL,
)
def cmd_status(args=None, app=None):
    if not app:
        return "No app context"

    lines = [
        "Galaxy Destroyer Status",
        "",
        f"Mode:      {app.state.mode}",
        f"CWD:       {app.context.cwd}",
        f"Messages:  {len(app.context.messages)}",
        f"History:   {len(app.state.history)}",
    ]
    return "\n".join(lines)


@register_command(
    name="env", description="Show environment", category=CommandCategory.SYSTEM
)
def cmd_env(args=None, app=None):
    lines = []
    for k, v in sorted(os.environ.items()):
        lines.append(f"{k}={v}")
    return "\n".join(lines)


@register_command(
    name="set",
    description="Set config options",
    category=CommandCategory.GENERAL,
    usage="set <key> [value]",
)
def cmd_set(args=None, app=None):
    if not args:
        return "Usage: set <key> [value]"

    key = args[0]
    if len(args) == 1:
        return f"Value for {key}: (not implemented)"

    value = args[1]

    if app:
        if key == "model":
            app.context.model = value
        elif key == "color":
            app.context.color = value.lower() == "true"

    return f"Set {key} = {value}"


@register_command(
    name="tools",
    description="List all available tools",
    category=CommandCategory.HELP,
    aliases=["list-tools", "tool-list"],
)
def cmd_tools(args=None, app=None):
    from tools.registry import tool_registry
    from tools.registry import ToolCategory

    category = None
    if args:
        cat_name = args[0].lower()
        for cat in ToolCategory:
            if cat.value == cat_name or cat.name.lower() == cat_name:
                category = cat
                break

    lines = ["=== Available Tools ===", ""]

    if category:
        tools = tool_registry.list_by_category(category)
        lines.append(f"Category: {category.value}")
        lines.append("")
        if tools:
            for tool in tools:
                lines.append(f"  {tool.name}")
                lines.append(f"    {tool.description}")
        else:
            lines.append("  No tools in this category")
    else:
        for cat in ToolCategory:
            tools = tool_registry.list_by_category(cat)
            if tools:
                lines.append(f"{cat.value.upper()} ({len(tools)}):")
                for tool in tools:
                    lines.append(f"  {tool.name}")
                lines.append("")

    lines.append(f"Total: {len(tool_registry.list_all())} tools")

    return "\n".join(lines)


@register_command(
    name="memory",
    description="Manage memory",
    category=CommandCategory.GENERAL,
    usage="memory [read|write|search]",
    examples=["memory read", "memory write"],
)
def cmd_memory(args=None, app=None):
    from core.memory import build_memory_prompt, get_auto_mem_path, ENTRYPOINT_NAME

    if not args:
        path = get_auto_mem_path()
        return f"""Memory Status:
  Path: {path}
  Entrypoint: {ENTRYPOINT_NAME}
  
Use 'memory read' to view MEMORY.md
Use 'memory write' to create/update MEMORY.md"""

    action = args[0].lower() if args else "read"

    if action == "read":
        from core.memory import read_memory_entrypoint

        content = read_memory_entrypoint()
        if content:
            return f"=== MEMORY.md ===\n\n{content}"
        return f"No MEMORY.md found at {get_auto_mem_path()}"

    elif action == "path":
        return f"Memory path: {get_auto_mem_path()}"

    elif action == "status":
        from services.tasks import get_task_store

        store = get_task_store()
        tasks = store.list(status="pending")
        return f"Tasks: {len(tasks)} pending"

    return f"Unknown action: {action}. Use: read, write, path, status"


@register_command(
    name="tasks",
    description="Manage tasks",
    category=CommandCategory.GENERAL,
    usage="tasks [list|create|done]",
    examples=["tasks list", "tasks create Fix bug", "tasks done task_123"],
)
def cmd_tasks(args=None, app=None):
    from services.tasks import get_task_store, TaskStatus

    store = get_task_store()

    if not args:
        tasks = store.list()[:10]
        lines = ["=== Tasks ===", ""]
        for task in tasks:
            status_icon = "✓" if task.status == TaskStatus.COMPLETED else "○"
            lines.append(f"{status_icon} [{task.status.value}] {task.title}")
        if not tasks:
            lines.append("No tasks")
        return "\n".join(lines)

    action = args[0].lower()

    if action == "list":
        status_filter = args[1] if len(args) > 1 else None
        tasks = store.list(status=status_filter)
        lines = [f"=== Tasks ({status_filter or 'all'}) ===", ""]
        for task in tasks:
            lines.append(f"[{task.status.value}] {task.title} ({task.id})")
        lines.append(f"\nTotal: {len(tasks)}")
        return "\n".join(lines)

    elif action == "create":
        if len(args) < 2:
            return "Usage: tasks create <title>"
        title = " ".join(args[1:])
        task = store.create(title)
        return f"Created: {task.id} - {task.title}"

    elif action == "done":
        if len(args) < 2:
            return "Usage: tasks done <task_id>"
        task_id = args[1]
        task = store.update(task_id, status="completed")
        if task:
            return f"Completed: {task.title}"
        return f"Task not found: {task_id}"

    elif action == "delete":
        if len(args) < 2:
            return "Usage: tasks delete <task_id>"
        task_id = args[1]
        if store.delete(task_id):
            return f"Deleted: {task_id}"
        return f"Task not found: {task_id}"

    return f"Unknown action: {action}"


@register_command(
    name="session",
    description="Manage sessions",
    category=CommandCategory.GENERAL,
    usage="session [list|new|switch]",
    examples=["session list", "session new MyProject"],
)
def cmd_session_cmd(args=None, app=None):
    from services.sessions import get_session_manager

    manager = get_session_manager()

    if not args:
        current = manager.get_current_session()
        return f"Current session: {current.id[:8] if current else 'none'}"

    action = args[0].lower()

    if action == "list":
        sessions = manager.list_sessions()
        lines = ["=== Sessions ===", ""]
        for session in sessions:
            lines.append(
                f"  {session['id'][:8]} - {session['title']} ({session['cwd']})"
            )
        lines.append(f"\nTotal: {len(sessions)}")
        return "\n".join(lines)

    elif action == "new":
        title = args[1] if len(args) > 1 else None
        session = manager.create_session(title=title)
        return f"New session: {session.id[:8]}"

    elif action == "switch":
        if len(args) < 2:
            return "Usage: session switch <session_id>"
        session_id = args[1]
        if manager.set_current_session(session_id):
            return f"Switched to: {session_id[:8]}"
        return f"Session not found: {session_id}"

    return f"Unknown action: {action}"
