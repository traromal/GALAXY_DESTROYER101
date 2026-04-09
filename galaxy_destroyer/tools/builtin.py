"""Built-in tools"""

import os
import subprocess
import json
import shlex
from typing import Any, Optional
from pathlib import Path

from .registry import register_tool, ToolCategory, ToolParameter


@register_tool(
    name="read_file",
    description="Read contents of a file",
    category=ToolCategory.FILE,
    parameters=[
        ToolParameter(name="path", description="Path to file", required=True),
        ToolParameter(
            name="offset", description="Start line", type="number", default=0
        ),
        ToolParameter(
            name="limit", description="Number of lines", type="number", default=2000
        ),
    ],
)
def read_file(path: str, offset: int = 0, limit: int = 2000, _context=None) -> dict:
    try:
        filepath = os.path.join(_context.cwd if _context else os.getcwd(), path)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)
        selected = lines[offset : offset + limit]

        return {
            "content": "".join(selected),
            "total_lines": total_lines,
            "showing": f"{offset + 1}-{min(offset + limit, total_lines)}",
        }
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="write_file",
    description="Write content to a file",
    category=ToolCategory.FILE,
    parameters=[
        ToolParameter(name="path", description="Path to file", required=True),
        ToolParameter(name="content", description="Content to write", required=True),
    ],
)
def write_file(path: str, content: str, _context=None) -> dict:
    try:
        cwd = _context.cwd if _context else os.getcwd()
        filepath = os.path.join(cwd, path)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True, "path": filepath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="list_directory",
    description="List files in a directory",
    category=ToolCategory.FILE,
    parameters=[
        ToolParameter(name="path", description="Directory path", default="."),
        ToolParameter(
            name="all", description="Show hidden files", type="boolean", default=False
        ),
    ],
)
def list_directory(path: str = ".", all: bool = False, _context=None) -> dict:
    try:
        cwd = _context.cwd if _context else os.getcwd()
        dirpath = os.path.join(cwd, path)

        if not os.path.exists(dirpath):
            return {"error": f"Directory not found: {path}"}

        entries = []
        for name in os.listdir(dirpath):
            if not all and name.startswith("."):
                continue

            full_path = os.path.join(dirpath, name)
            stat = os.stat(full_path)

            entries.append(
                {
                    "name": name,
                    "type": "directory" if os.path.isdir(full_path) else "file",
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                }
            )

        entries.sort(key=lambda x: (x["type"] != "directory", x["name"]))

        return {"entries": entries, "path": dirpath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="search",
    description="Search for text in files",
    category=ToolCategory.SEARCH,
    parameters=[
        ToolParameter(
            name="pattern", description="Search pattern (regex)", required=True
        ),
        ToolParameter(name="path", description="Directory to search", default="."),
        ToolParameter(name="include", description="File pattern", default="*"),
    ],
)
def search(pattern: str, path: str = ".", include: str = "*", _context=None) -> dict:
    try:
        import re

        cwd = _context.cwd if _context else os.getcwd()
        search_path = os.path.join(cwd, path)

        regex = re.compile(pattern)
        matches = []

        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in files:
                if not self._matches_pattern(filename, include):
                    continue

                filepath = os.path.join(root, filename)

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if regex.search(line):
                                matches.append(
                                    {
                                        "file": os.path.relpath(filepath, cwd),
                                        "line": line_no,
                                        "text": line.rstrip(),
                                    }
                                )
                                if len(matches) >= 100:
                                    break
                except:
                    pass

                if len(matches) >= 100:
                    break

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}


def _matches_pattern(filename: str, pattern: str) -> bool:
    if pattern == "*":
        return True
    import fnmatch

    return fnmatch.fnmatch(filename, pattern)


@register_tool(
    name="run_shell",
    description="Run a shell command",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(name="command", description="Command to run", required=True),
        ToolParameter(
            name="timeout", description="Timeout in seconds", type="number", default=60
        ),
    ],
)
def run_shell(command: str, timeout: int = 60, _context=None) -> dict:
    try:
        cwd = _context.cwd if _context else os.getcwd()

        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="git_status", description="Show git status", category=ToolCategory.GIT
)
def git_status(_context=None) -> dict:
    try:
        cwd = _context.cwd if _context else os.getcwd()

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {"error": "Not a git repository"}

        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2]
                filename = line[3:]
                files.append({"status": status, "file": filename})

        return {"files": files, "clean": len(files) == 0}
    except FileNotFoundError:
        return {"error": "Git not installed"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="git_log",
    description="Show git commit history",
    category=ToolCategory.GIT,
    parameters=[
        ToolParameter(
            name="limit", description="Number of commits", type="number", default=10
        ),
    ],
)
def git_log(limit: int = 10, _context=None) -> dict:
    try:
        cwd = _context.cwd if _context else os.getcwd()

        result = subprocess.run(
            ["git", "log", f"-n={limit}", "--oneline", "--format=%h|%s|%an"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {"error": "Not a git repository"}

        commits = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) >= 3:
                    commits.append(
                        {
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                        }
                    )

        return {"commits": commits}
    except FileNotFoundError:
        return {"error": "Git not installed"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="read_memory",
    description="Read the user's memory file (MEMORY.md)",
    category=ToolCategory.MEMORY,
)
def read_memory(_context=None) -> dict:
    from core.memory import read_memory_entrypoint, get_auto_mem_path, ENTRYPOINT_NAME

    content = read_memory_entrypoint()

    if content:
        return {
            "content": content,
            "path": get_auto_mem_path(),
            "entrypoint": ENTRYPOINT_NAME,
        }

    return {
        "content": None,
        "message": f"No {ENTRYPOINT_NAME} found. Use write_memory to create one.",
        "path": get_auto_mem_path(),
    }


@register_tool(
    name="write_memory",
    description="Write content to MEMORY.md or a memory file",
    category=ToolCategory.MEMORY,
    parameters=[
        ToolParameter(name="content", description="Content to write", required=True),
        ToolParameter(
            name="filename",
            description="Filename (default: MEMORY.md)",
            default="MEMORY.md",
        ),
    ],
)
def write_memory(content: str, filename: str = "MEMORY.md", _context=None) -> dict:
    from core.memory import write_memory_entrypoint, get_auto_mem_path, ENTRYPOINT_NAME

    if filename == ENTRYPOINT_NAME:
        write_memory_entrypoint(content)
        return {
            "success": True,
            "message": f"Updated {ENTRYPOINT_NAME}",
            "path": get_auto_mem_path(),
        }
    else:
        import os

        filepath = os.path.join(get_auto_mem_path(), filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "message": f"Saved memory: {filename}",
            "path": filepath,
        }


@register_tool(
    name="append_memory",
    description="Append content to MEMORY.md (adds a new entry)",
    category=ToolCategory.MEMORY,
    parameters=[
        ToolParameter(
            name="entry", description="Memory entry to append", required=True
        ),
    ],
)
def append_memory(entry: str, _context=None) -> dict:
    from core.memory import (
        read_memory_entrypoint,
        write_memory_entrypoint,
        ENTRYPOINT_NAME,
    )

    existing = read_memory_entrypoint() or ""

    if existing:
        if not existing.endswith("\n"):
            existing += "\n"
        new_content = existing + entry + "\n"
    else:
        new_content = entry + "\n"

    write_memory_entrypoint(new_content)

    return {
        "success": True,
        "message": "Appended to MEMORY.md",
    }


@register_tool(
    name="get_config",
    description="Get configuration value",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(name="key", description="Config key", required=True),
    ],
)
def get_config(key: str, _context=None) -> dict:
    config_file = os.path.expanduser("~/.galaxy_destroyer_config.json")

    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)

            if key in config:
                return {"key": key, "value": config[key]}

        return {"error": f"Config key not found: {key}"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="set_config",
    description="Set configuration value",
    category=ToolCategory.SYSTEM,
    parameters=[
        ToolParameter(name="key", description="Config key", required=True),
        ToolParameter(name="value", description="Config value", required=True),
    ],
)
def set_config(key: str, value: Any, _context=None) -> dict:
    config_file = os.path.expanduser("~/.galaxy_destroyer_config.json")

    try:
        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)

        config[key] = value

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        return {"success": True, "key": key, "value": value}
    except Exception as e:
        return {"error": str(e)}
