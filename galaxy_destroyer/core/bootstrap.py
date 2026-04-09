"""Bootstrap and state management - initializes app state"""

import os
import time
import platform
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
import uuid


@dataclass
class AppBootstrapState:
    cwd: str = ""
    original_cwd: str = ""
    session_id: str = ""
    is_interactive: bool = True
    is_non_interactive: bool = False
    client_type: str = "cli"
    model_override: Optional[str] = None
    agent_type: Optional[str] = None
    settings_path: Optional[str] = None
    plugin_dirs: list = field(default_factory=list)
    inline_plugins: list = field(default_factory=list)
    sdk_url: Optional[str] = None
    entrypoint: str = "cli"
    startup_time: float = 0


_bootstrap_state = AppBootstrapState()


def bootstrap_init() -> AppBootstrapState:
    global _bootstrap_state

    _bootstrap_state.cwd = os.getcwd()
    _bootstrap_state.original_cwd = _bootstrap_state.cwd
    _bootstrap_state.session_id = str(uuid.uuid4())[:8]
    _bootstrap_state.startup_time = time.time()

    try:
        _bootstrap_state.is_interactive = os.isatty(0)
    except:
        _bootstrap_state.is_interactive = True

    if not _bootstrap_state.is_interactive:
        _bootstrap_state.is_non_interactive = True
        _bootstrap_state.client_type = "sdk-cli"
        _bootstrap_state.entrypoint = "sdk-cli"

    return _bootstrap_state


def get_bootstrap_state() -> AppBootstrapState:
    global _bootstrap_state
    if not _bootstrap_state.cwd:
        bootstrap_init()
    return _bootstrap_state


def get_cwd() -> str:
    return _bootstrap_state.cwd or os.getcwd()


def get_session_id() -> str:
    return _bootstrap_state.session_id


def is_interactive() -> bool:
    return _bootstrap_state.is_interactive


def get_client_type() -> str:
    return _bootstrap_state.client_type


@dataclass
class SystemInfo:
    os_type: str = ""
    os_version: str = ""
    os_release: str = ""
    cwd: str = ""
    hostname: str = ""
    username: str = ""

    @classmethod
    def collect(cls) -> "SystemInfo":
        info = cls()
        info.os_type = platform.system()
        info.os_version = platform.version()
        info.os_release = platform.release()
        info.cwd = get_cwd()
        info.hostname = platform.node()
        info.username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
        return info


@dataclass
class SessionInfo:
    id: str = ""
    start_time: float = 0
    project_dir: str = ""
    is_git: bool = False
    git_branch: str = ""

    @classmethod
    def create(cls, project_dir: str = None) -> "SessionInfo":
        info = cls()
        info.id = get_session_id()
        info.start_time = time.time()
        info.project_dir = project_dir or get_cwd()
        info.is_git = cls._is_git_repo(info.project_dir)
        if info.is_git:
            info.git_branch = cls._get_git_branch(info.project_dir)
        return info

    @staticmethod
    def _is_git_repo(path: str) -> bool:
        return os.path.isdir(os.path.join(path, ".git"))

    @staticmethod
    def _get_git_branch(path: str) -> str:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or "main"
        except:
            return "main"


def get_model_info(model: str) -> Dict[str, str]:
    model_info = {
        "qwen2.5-coder": {
            "description": "Code-specialized model, fast and capable",
            "best_for": "Code completion, debugging, general coding",
        },
        "llama3": {
            "description": "General purpose model",
            "best_for": "General reasoning, conversation",
        },
        "gpt-4": {
            "description": "OpenAI's GPT-4",
            "best_for": "Complex reasoning, high quality code",
        },
        "claude-opus-4-5-20251114": {
            "description": "Anthropic's Claude",
            "best_for": "High-quality assistance, complex tasks",
        },
    }
    return model_info.get(
        model, {"description": "Unknown model", "best_for": "General use"}
    )


def get_backend_info(backend: str) -> Dict[str, Any]:
    backend_info = {
        "opencode": {
            "name": "OpenCode.ai",
            "url": "https://opencode.ai/api",
            "default_model": "qwen2.5-coder",
            "requires_key": False,
            "description": "Free, open source AI backend",
        },
        "ollama": {
            "name": "Ollama",
            "url": "http://localhost:11434",
            "default_model": "llama3",
            "requires_key": False,
            "description": "Local models",
        },
        "openai": {
            "name": "OpenAI",
            "url": "https://api.openai.com/v1",
            "default_model": "gpt-4",
            "requires_key": True,
            "description": "OpenAI API",
        },
        "anthropic": {
            "name": "Anthropic",
            "url": "https://api.anthropic.com",
            "default_model": "claude-opus-4-5-20251114",
            "requires_key": True,
            "description": "Anthropic Claude API",
        },
    }
    return backend_info.get(backend, {})


def format_welcome_message(model: str, backend: str) -> str:
    backend_info = get_backend_info(backend)
    model_info = get_model_info(model)

    return f"""
╔════════════════════════════════════════════════════════════════╗
║                   GALAXY DESTROYER v0.1.0                     ║
║                   AI-Powered Terminal Assistant                ║
╚════════════════════════════════════════════════════════════════╝

Backend: {backend_info.get("name", backend)}
Model:   {model}
{backend_info.get("description", "")}

Type your request to start. Examples:
  • "Write a function to calculate fibonacci"
  • "Fix the bug in src/main.py"
  • "Explore the codebase structure"
  • "Review my latest changes"

Commands:
  /help     - Show all commands
  /status   - Show current status
  /tools    - List available tools
  /agents   - List available agents
  /clear    - Clear conversation
  /exit     - Exit Galaxy Destroyer

"""


def format_status(model: str, backend: str, session: SessionInfo = None) -> str:
    if session is None:
        session = SessionInfo.create()

    return f"""
=== Galaxy Destroyer Status ===
Backend: {backend} ({get_backend_info(backend).get("name", "")})
Model:   {model}
Session: {session.id}
CWD:     {session.project_dir}
Git:     {"Yes (" + session.git_branch + ")" if session.is_git else "No"}
"""


def build_full_system_prompt(
    model: str = "qwen2.5-coder",
    backend: str = "opencode",
    custom_prompt: str = None,
) -> str:
    """Build the complete system prompt"""

    system_info = SystemInfo.collect()
    session_info = SessionInfo.create()

    parts = [
        get_system_prompt(model, backend, system_info, session_info),
        get_capabilities_prompt(),
        get_tool_use_prompt([]),
    ]

    if custom_prompt:
        parts.append(f"\n\n== Custom Instructions ==\n{custom_prompt}")

    return "\n\n".join(parts)


def get_system_prompt(
    model: str = "qwen2.5-coder",
    backend: str = "opencode",
    system_info: SystemInfo = None,
    session_info: SessionInfo = None,
) -> str:
    """Build the main system prompt similar to Claude Code"""

    if system_info is None:
        system_info = SystemInfo.collect()
    if session_info is None:
        session_info = SessionInfo.create()

    return f"""You are Galaxy Destroyer, an AI coding assistant built in Python.

== System Info ==
- OS: {system_info.os_type} {system_info.os_release}
- Hostname: {system_info.hostname}
- User: {system_info.username}
- Current directory: {system_info.cwd}

== Session Info ==
- Session ID: {session_info.id}
- Project: {session_info.project_dir}
- Git: {"Yes" if session_info.is_git else "No"}
- Branch: {session_info.git_branch if session_info.is_git else "N/A"}

== Model & Backend ==
- Model: {model}
- Backend: {backend}

== Guidelines ==
1. You have access to tools for file operations, git, shell commands, web search, and more
2. Always verify changes before reporting completion
3. Be thorough but efficient - complete tasks fully without gold-plating
4. Use agents (explore, verification, code_review, etc.) for complex tasks
5. Handle errors gracefully and explain issues clearly
6. Use vim mode if editing text (press i for insert, Escape to return to normal mode)"""


def get_tool_use_prompt(tools_schema: List = None) -> str:
    return """== Tool Usage Guidelines ==

When you need to perform actions, use the available tools:
- Use Read instead of cat, head, tail
- Use Edit instead of sed or awk
- Use Write instead of cat with heredoc
- Use Glob instead of find
- Use Grep instead of grep or rg
- Reserve Bash for system commands"""


def get_capabilities_prompt() -> str:
    return """== Galaxy Destroyer Capabilities ==

Galaxy Destroyer is a terminal-based AI coding assistant that can:

**Code Assistance:**
- Write new code in any language
- Edit and refactor existing code
- Debug issues and fix bugs
- Review code for quality and security
- Write tests (unit, integration, e2e)

**Codebase Exploration:**
- Search for files by pattern (glob)
- Search for code content (grep)
- Read and analyze files
- Understand project structure

**Shell & Git:**
- Run any terminal command
- Manage git repositories
- Execute build scripts, tests, linters

**Web:**
- Fetch web pages
- Search the web for information

**Task Management:**
- Create and track tasks
- Manage todo lists

**Agents:**
- Explore: Fast file searching
- Verification: Test and verify implementations
- Code Review: Review code changes
- Debug: Find and fix bugs
- Write: Implement features
- Test: Write test cases
- Refactor: Improve code quality"""
