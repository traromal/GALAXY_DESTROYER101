"""System prompts and bootstrap - full Claude Code-style system prompt"""

import os
import platform
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class SystemInfo:
    """System information for prompt"""
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
        info.cwd = os.getcwd()
        info.hostname = platform.node()
        info.username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
        return info


@dataclass 
class SessionInfo:
    """Session information"""
    id: str = ""
    start_time: float = 0
    project_dir: str = ""
    is_git: bool = False
    git_branch: str = ""
    worktree: Optional[str] = None
    
    @classmethod
    def create(cls, project_dir: str = None) -> "SessionInfo":
        import time
        import uuid
        info = cls()
        info.id = str(uuid.uuid4())[:8]
        info.start_time = time.time()
        info.project_dir = project_dir or os.getcwd()
        
        info.is_git = cls._is_git_repo(info.project_dir)
        if info.is_git:
            info.git_branch = cls._get_git_branch(info.project_dir)
        
        return info
    
    @staticmethod
    def _is_git_repo(path: str) -> bool:
        return os.path.isdir(os.path.join(path, ".git"))
    
    @staticmethod
    def _get_git_branch(path: str) -> str:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path, capture_output=True, text=True
            )
            return result.stdout.strip() or "main"
        except:
            return "main"


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
    
    prompt = f"""You are Galaxy Destroyer, an AI coding assistant built in Python. Your role is to help users with software development tasks including writing code, debugging, exploring codebases, and running commands.

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
6. Use vim mode if editing text (press i for insert, Escape to return to normal mode)

== Available Tools ==
- File operations: read_file, write_file, edit_file, delete_file, move_file, glob, grep
- Shell: bash, run_shell, get_env
- Git: git_status, git_log, git_diff, git_commit, git_push, git_pull
- Web: web_fetch, web_search  
- Tasks: task_create, task_get, task_list, task_update, task_delete, todo_write
- Skills: skill_list, skill_execute
- Config: config_get, config_set
- Agents: agent (use for explore, verification, code_review, write, debug, test, refactor)

== Important Notes ==
- The user is working in: {system_info.cwd}
- Use relative paths when possible
- Always check git status before making commits
- When verifying implementation, run actual tests/commands, don't just read code
- Report completion with a summary of what was done

You are ready to help with coding tasks. Wait for the user's input."""
    
    return prompt


def get_tool_use_prompt(tools_schema: List[Dict]) -> str:
    """Build tool usage instructions"""
    
    prompt = """== Tool Usage Guidelines ==

When you need to perform actions, use the available tools. Here's how:

**Reading Files:**
- Use read_file for specific file paths
- Use glob for finding files by pattern
- Use grep for searching file contents

**File Operations:**
- Use write_file to create new files or overwrite
- Use edit_file to modify existing files (specify old_string and new_string)
- Use delete_file to remove files
- Use move_file to rename/move files

**Shell Commands:**
- Use bash to run commands (ls, cd, git, npm, pip, etc.)
- Commands run in the current working directory

**Git:**
- git_status: Check repository state
- git_log: View commit history
- git_diff: See changes
- git_commit: Commit changes (requires message)
- git_push: Push to remote
- git_pull: Pull from remote

**Tasks:**
- task_create: Create a new task
- task_list: List all tasks
- task_update: Update task status

**Agents:**
- agent with name="explore" for searching codebases
- agent with name="verification" for verifying implementations  
- agent with name="code_review" for reviewing code
- agent with name="debug" for debugging issues
- agent with name="test" for writing tests
- agent with name="write" for implementing features
- agent with name="refactor" for improving code
- agent with name="plan" for planning complex tasks

Always explain what you're doing before running tools. Report results clearly."""
    
    return prompt


def get_capabilities_prompt() -> str:
    """Build capabilities description"""
    
    return """== Galaxy Destroyer Capabilities ==

Galaxy Destroyer is a terminal-based AI coding assistant that can:

**Code Assistance:**
- Write new code in any language
- Edit and refactor existing code
- Debug issues and fix bugs
- Review code for quality and security
- Write tests (unit, integration, e2e)

**Codebase Exploration:**
- Search for files by name pattern (glob)
- Search for code content (grep)
- Read and analyze files
- Understand project structure

**Shell & Git:**
- Run any terminal command
- Manage git repositories (status, commit, push, pull, branches)
- Execute build scripts, tests, linters

**Web:**
- Fetch web pages
- Search the web for information

**Task Management:**
- Create and track tasks
- Manage todo lists
- Update task status

**Project Context:**
- Remember project-specific information
- Understand file relationships
- Build context from project structure

**Agents:**
- Use specialized agents for complex tasks
- Explore: Fast file searching
- Verification: Test and verify implementations
- Code Review: Review code changes
- Debug: Find and fix bugs
- Write: Implement features
- Test: Write test cases
- Refactor: Improve code quality

The assistant can handle multi-step tasks, coordinate between tools, and provide clear feedback."""


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


def get_model_info(model: str) -> Dict[str, str]:
    """Get model information and recommendations"""
    
    model_info = {
        "qwen2.5-coder": {
            "description": "Code-specialized model, fast and capable",
            "best_for": "Code completion, debugging, general coding",
        },
        "llama3": {
            "description": "General purpose model from Meta",
            "best_for": "General reasoning, conversation",
        },
        "gpt-4": {
            "description": "OpenAI's GPT-4",
            "best_for": "Complex reasoning, high-quality code",
        },
        "claude-opus-4-5-20251114": {
            "description": "Anthropic's Claude",
            "best_for": "High-quality assistance, complex tasks",
        },
    }
    
    return model_info.get(model, {"description": "Unknown model", "best_for": "General use"})


def get_backend_info(backend: str) -> Dict[str, Any]:
    """Get backend information"""
    
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
            "description": "Local models - run on your machine",
        },
        "openai": {
            "name": "OpenAI",
            "url": "https://api.openai.com/v1",
            "default_model": "gpt-4",
            "requires_key": True,
            "description": "OpenAI API - GPT models",
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
    """Format the welcome message"""
    
    backend_info = get_backend_info(backend)
    model_info = get_model_info(model)
    
    msg = f"""
╔════════════════════════════════════════════════════════════════╗
║                   GALAXY DESTROYER v0.1.0                     ║
║                   AI-Powered Terminal Assistant                ║
╚════════════════════════════════════════════════════════════════╝

Backend: {backend_info.get('name', backend)}
Model:   {model}
{backend_info.get('description', '')}

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
    
    return msg


def format_status(model: str, backend: str, session: SessionInfo = None) -> str:
    """Format status message"""
    
    if session is None:
        session = SessionInfo.create()
    
    return f"""
=== Galaxy Destroyer Status ===
Backend: {backend} ({get_backend_info(backend).get('name', '')})
Model:   {model}
Session: {session.id}
CWD:     {session.project_dir}
Git:     {'Yes (' + session.git_branch + ')' if session.is_git else 'No'}
"""