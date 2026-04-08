"""Built-in tools - file operations, git, search, shell"""

import os
import subprocess
import json
import re
import asyncio
import fnmatch
from typing import Any, Optional, Dict, List
from pathlib import Path

from .executor import register_tool


def _get_cwd(context: Any) -> str:
    return context.cwd if context and hasattr(context, 'cwd') else os.getcwd()


@register_tool(
    name="read_file",
    description="Read contents of a file",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "offset": {"type": "integer", "description": "Start line", "default": 0},
            "limit": {"type": "integer", "description": "Number of lines", "default": 2000}
        },
        "required": ["path"]
    }
)
def read_file(path: str, offset: int = 0, limit: int = 2000, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        filepath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        if not os.path.exists(filepath):
            return {"error": f"File not found: {path}"}
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        total = len(lines)
        selected = lines[offset:offset + limit]
        
        return {
            "content": "".join(selected),
            "total_lines": total,
            "showing": f"{offset+1}-{min(offset+limit, total)}",
            "path": filepath
        }
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="write_file",
    description="Write content to a file",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "content": {"type": "string", "description": "Content to write"}
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        filepath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"success": True, "path": filepath, "bytes_written": len(content)}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="edit_file",
    description="Edit a file by replacing text",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"},
            "old_string": {"type": "string", "description": "Text to replace"},
            "new_string": {"type": "string", "description": "Replacement text"}
        },
        "required": ["path", "old_string", "new_string"]
    }
)
def edit_file(path: str, old_string: str, new_string: str, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        filepath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_string not in content:
            return {"error": "String not found in file"}
        
        new_content = content.replace(old_string, new_string, 1)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="list_directory",
    description="List files in a directory",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path", "default": "."},
            "all": {"type": "boolean", "description": "Show hidden files", "default": False}
        }
    }
)
def list_directory(path: str = ".", all: bool = False, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        dirpath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        if not os.path.exists(dirpath):
            return {"error": f"Directory not found: {path}"}
        
        entries = []
        for name in sorted(os.listdir(dirpath)):
            if not all and name.startswith('.'):
                continue
            
            full = os.path.join(dirpath, name)
            stat = os.stat(full)
            
            entries.append({
                "name": name,
                "type": "directory" if os.path.isdir(full) else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
        
        return {"entries": entries, "path": dirpath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="search_files",
    description="Search for text in files",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "path": {"type": "string", "description": "Directory to search", "default": "."},
            "include": {"type": "string", "description": "File pattern", "default": "*"},
            "exclude": {"type": "string", "description": "Exclude pattern", "default": ""}
        },
        "required": ["pattern"]
    }
)
def search_files(pattern: str, path: str = ".", include: str = "*", exclude: str = "", _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        search_path = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        regex = re.compile(pattern)
        matches = []
        
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if not fnmatch.fnmatch(filename, include):
                    continue
                if exclude and fnmatch.fnmatch(filename, exclude):
                    continue
                
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for lineno, line in enumerate(f, 1):
                            if regex.search(line):
                                relpath = os.path.relpath(filepath, cwd)
                                matches.append({
                                    "file": relpath,
                                    "line": lineno,
                                    "text": line.rstrip()[:200]
                                })
                                if len(matches) >= 100:
                                    break
                except:
                    pass
                
                if len(matches) >= 100:
                    break
        
        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="run_shell",
    description="Run a shell command",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run"},
            "timeout": {"type": "number", "description": "Timeout in seconds", "default": 60}
        },
        "required": ["command"]
    }
)
def run_shell(command: str, timeout: float = 60.0, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="git_status",
    description="Show git status",
    parameters={"type": "object", "properties": {}}
)
def git_status(_context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {"error": "Not a git repository", "is_git": False}
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2].strip()
                filename = line[3:]
                files.append({"status": status, "file": filename})
        
        return {"files": files, "clean": len(files) == 0, "is_git": True}
    except FileNotFoundError:
        return {"error": "Git not installed", "is_git": False}
    except Exception as e:
        return {"error": str(e), "is_git": False}


@register_tool(
    name="git_log",
    description="Show git commit history",
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 10}
        }
    }
)
def git_log(limit: int = 10, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        
        result = subprocess.run(
            ["git", "log", f"-n={limit}", "--oneline", "--format=%h|%s|%an|%ad", "--date=short"],
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {"error": "Not a git repository"}
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "author": parts[2],
                        "date": parts[3]
                    })
        
        return {"commits": commits}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="git_diff",
    description="Show git diff",
    parameters={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "File to diff"}
        }
    }
)
def git_diff(file: str = "", _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        
        cmd = ["git", "diff"]
        if file:
            cmd.append(file)
        
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        
        return {"diff": result.stdout[:20000]}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="get_config",
    description="Get configuration value",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"}
        },
        "required": ["key"]
    }
)
def get_config(key: str, _context: Any = None) -> Dict:
    config_file = os.path.expanduser("~/.galaxy_destroyer_config.json")
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if key in config:
                return {"key": key, "value": config[key]}
        
        return {"error": f"Config key not found: {key}"}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="set_config",
    description="Set configuration value",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"},
            "value": {"type": "string", "description": "Config value"}
        },
        "required": ["key", "value"]
    }
)
def set_config(key: str, value: Any, _context: Any = None) -> Dict:
    config_file = os.path.expanduser("~/.galaxy_destroyer_config.json")
    
    try:
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        config[key] = value
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {"success": True, "key": key, "value": value}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="create_directory",
    description="Create a directory",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path"}
        },
        "required": ["path"]
    }
)
def create_directory(path: str, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        dirpath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        os.makedirs(dirpath, exist_ok=True)
        
        return {"success": True, "path": dirpath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="delete_file",
    description="Delete a file or directory",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to delete"},
            "recursive": {"type": "boolean", "default": False}
        },
        "required": ["path"]
    }
)
def delete_file(path: str, recursive: bool = False, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        filepath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        if not os.path.exists(filepath):
            return {"error": f"Path not found: {path}"}
        
        if os.path.isdir(filepath):
            if recursive:
                import shutil
                shutil.rmtree(filepath)
            else:
                os.rmdir(filepath)
        else:
            os.remove(filepath)
        
        return {"success": True, "path": filepath}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="move_file",
    description="Move or rename a file/directory",
    parameters={
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Source path"},
            "destination": {"type": "string", "description": "Destination path"}
        },
        "required": ["source", "destination"]
    }
)
def move_file(source: str, destination: str, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        src = os.path.join(cwd, source) if not os.path.isabs(source) else source
        dst = os.path.join(cwd, destination) if not os.path.isabs(destination) else destination
        
        os.rename(src, dst)
        
        return {"success": True, "from": src, "to": dst}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="get_env",
    description="Get environment variable",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Variable name"}
        },
        "required": ["name"]
    }
)
def get_env(name: str, _context: Any = None) -> Dict:
    value = os.environ.get(name)
    if value is None:
        return {"error": f"Environment variable not found: {name}"}
    return {"name": name, "value": value}


@register_tool(
    name="glob_files",
    description="Find files matching pattern",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern"},
            "path": {"type": "string", "default": "."}
        },
        "required": ["pattern"]
    }
)
def glob_files(pattern: str, path: str = ".", _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        search_path = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        matches = []
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    full = os.path.join(root, filename)
                    rel = os.path.relpath(full, cwd)
                    matches.append(rel)
        
        return {"files": matches, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="file_info",
    description="Get file/directory information",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to file"}
        },
        "required": ["path"]
    }
)
def file_info(path: str, _context: Any = None) -> Dict:
    try:
        cwd = _get_cwd(_context)
        filepath = os.path.join(cwd, path) if not os.path.isabs(path) else path
        
        if not os.path.exists(filepath):
            return {"error": f"Path not found: {path}"}
        
        stat = os.stat(filepath)
        
        return {
            "path": filepath,
            "type": "directory" if os.path.isdir(filepath) else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime
        }
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="bash",
    description="Execute shell commands",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to execute"},
            "timeout": {"type": "number", "description": "Timeout in seconds", "default": 60},
            "description": {"type": "string", "description": "Command description"}
        },
        "required": ["command"]
    }
)
def bash(command: str, timeout: float = 60.0, description: str = "", _context: Any = None) -> Dict:
    return run_shell(command, timeout, _context)


@register_tool(
    name="glob",
    description="Find files by pattern",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern"},
            "path": {"type": "string", "default": "."}
        },
        "required": ["pattern"]
    }
)
def glob(pattern: str, path: str = ".", _context: Any = None) -> Dict:
    return glob_files(pattern, path, _context)


@register_tool(
    name="grep",
    description="Search for text patterns in files",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Search pattern"},
            "path": {"type": "string", "default": "."},
            "include": {"type": "string", "default": "*"}
        },
        "required": ["pattern"]
    }
)
def grep(pattern: str, path: str = ".", include: str = "*", _context: Any = None) -> Dict:
    return search_files(pattern, path, include, "", _context)


@register_tool(
    name="web_fetch",
    description="Fetch web page content",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        },
        "required": ["url"]
    }
)
def web_fetch(url: str, _context: Any = None) -> Dict:
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='replace')
            return {"content": content[:50000], "url": url, "status": 200}
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="web_search",
    description="Search the web for information using DuckDuckGo",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results", "default": 10}
        },
        "required": ["query"]
    }
)
def web_search(query: str, num_results: int = 10, _context: Any = None) -> Dict:
    """Search the web using DuckDuckGo HTML"""
    try:
        import urllib.request
        import urllib.parse
        import re
        
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8', errors='replace')
        
        results = []
        result_pattern = r'<a class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?<a class="result__snippet"[^>]*>([^<]*)</a>'
        
        matches = re.findall(result_pattern, html)
        
        for i, (url_match, title_match, snippet_match) in enumerate(matches[:num_results]):
            results.append({
                "title": title_match.strip(),
                "url": url_match.strip(),
                "snippet": snippet_match.strip()[:200],
            })
        
        if not results:
            return {"error": "No results found", "query": query}
        
        return {
            "results": results,
            "count": len(results),
            "query": query,
        }
    except Exception as e:
        return {"error": str(e), "query": query}


@register_tool(
    name="mcp_list_resources",
    description="List MCP server resources",
    parameters={
        "type": "object",
        "properties": {
            "server": {"type": "string", "description": "MCP server name"}
        }
    }
)
def mcp_list_resources(server: str = "", _context: Any = None) -> Dict:
    """List MCP server resources - placeholder for MCP integration"""
    return {
        "servers": [],
        "message": "MCP support available. Configure MCP servers in .claude/mcp.json",
    }


@register_tool(
    name="mcp_read_resource",
    description="Read MCP resource",
    parameters={
        "type": "object",
        "properties": {
            "uri": {"type": "string", "description": "Resource URI (e.g., mcp://server/resource")"}
        },
        "required": ["uri"]
    }
)
def mcp_read_resource(uri: str, _context: Any = None) -> Dict:
    """Read a resource from MCP server"""
    if not uri.startswith("mcp://"):
        return {"error": "Invalid URI format. Use mcp://server/resource"}
    
    parts = uri.replace("mcp://", "").split("/", 1)
    server = parts[0]
    resource = parts[1] if len(parts) > 1 else ""
    
    return {
        "error": "MCP server not connected",
        "server": server,
        "resource": resource,
    }


@register_tool(
    name="mcp_call_tool",
    description="Call a tool on an MCP server",
    parameters={
        "type": "object",
        "properties": {
            "server": {"type": "string", "description": "MCP server name"},
            "tool": {"type": "string", "description": "Tool name to call"},
            "arguments": {"type": "object", "description": "Tool arguments"}
        },
        "required": ["server", "tool"]
    }
)
def mcp_call_tool(server: str, tool: str, arguments: Dict = None, _context: Any = None) -> Dict:
    """Call a tool on an MCP server"""
    return {
        "error": "MCP server not connected",
        "server": server,
        "tool": tool,
        "arguments": arguments or {},
    }


@register_tool(
    name="mcp_call_tool",
    description="Call MCP server tool",
    parameters={
        "type": "object",
        "properties": {
            "server": {"type": "string", "description": "MCP server"},
            "tool": {"type": "string", "description": "Tool name"},
            "arguments": {"type": "object", "description": "Tool arguments"}
        },
        "required": ["server", "tool"]
    }
)
def mcp_call_tool(server: str, tool: str, arguments: Dict = None, _context: Any = None) -> Dict:
    return {"error": "MCP not configured", "server": server, "tool": tool}


@register_tool(
    name="enter_worktree",
    description="Enter git worktree",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Worktree path"}
        },
        "required": ["path"]
    }
)
def enter_worktree(path: str, _context: Any = None) -> Dict:
    cwd = _get_cwd(_context)
    result = subprocess.run(["git", "worktree", "list"], cwd=cwd, capture_output=True, text=True)
    return {"worktrees": result.stdout.split('\n') if result.returncode == 0 else []}


@register_tool(
    name="exit_worktree",
    description="Exit git worktree",
    parameters={"type": "object", "properties": {}}
)
def exit_worktree(_context: Any = None) -> Dict:
    return {"message": "Use cd to exit worktree"}


@register_tool(
    name="lsp_symbols",
    description="Get language server symbols",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"}
        }
    }
)
def lsp_symbols(path: str = "", _context: Any = None) -> Dict:
    return {"error": "LSP server not connected"}


@register_tool(
    name="lsp_definition",
    description="Go to definition",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "line": {"type": "integer", "description": "Line number"},
            "character": {"type": "integer", "description": "Character position"}
        },
        "required": ["path", "line"]
    }
)
def lsp_definition(path: str, line: int, character: int = 0, _context: Any = None) -> Dict:
    return {"error": "LSP server not connected"}


@register_tool(
    name="lsp_references",
    description="Find references",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "line": {"type": "integer"},
            "character": {"type": "integer"}
        },
        "required": ["path", "line"]
    }
)
def lsp_references(path: str, line: int, character: int = 0, _context: Any = None) -> Dict:
    return {"error": "LSP server not connected"}


@register_tool(
    name="enter_plan_mode",
    description="Enter planning mode",
    parameters={
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "Plan goal"}
        }
    }
)
def enter_plan_mode(goal: str = "", _context: Any = None) -> Dict:
    return {"mode": "plan", "goal": goal}


@register_tool(
    name="exit_plan_mode",
    description="Exit planning mode",
    parameters={
        "type": "object",
        "properties": {
            "accept": {"type": "boolean", "description": "Accept plan"}
        }
    }
)
def exit_plan_mode(accept: bool = False, _context: Any = None) -> Dict:
    return {"mode": "normal", "accepted": accept}


@register_tool(
    name="task_create",
    description="Create a task",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title"},
            "description": {"type": "string", "description": "Task description"}
        },
        "required": ["title"]
    }
)
def task_create(title: str, description: str = "", _context: Any = None) -> Dict:
    return {"id": "task_" + str(hash(title))[:8], "title": title, "status": "pending"}


@register_tool(
    name="task_update",
    description="Update a task",
    parameters={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Task ID"},
            "status": {"type": "string", "description": "New status"}
        },
        "required": ["id"]
    }
)
def task_update(id: str, status: str = "", _context: Any = None) -> Dict:
    return {"id": id, "status": status, "updated": True}


@register_tool(
    name="task_get",
    description="Get task details",
    parameters={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Task ID"}
        },
        "required": ["id"]
    }
)
def task_get(id: str, _context: Any = None) -> Dict:
    return {"id": id, "title": "Task", "status": "pending"}


@register_tool(
    name="task_list",
    description="List all tasks",
    parameters={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter by status"}
        }
    }
)
def task_list(status: str = "", _context: Any = None) -> Dict:
    return {"tasks": [], "count": 0}


@register_tool(
    name="task_stop",
    description="Stop a running task",
    parameters={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "Task ID"}
        },
        "required": ["id"]
    }
)
def task_stop(id: str, _context: Any = None) -> Dict:
    return {"id": id, "stopped": True}


@register_tool(
    name="todo_write",
    description="Write to todo list",
    parameters={
        "type": "object",
        "properties": {
            "todos": {"type": "array", "description": "Todo items"}
        },
        "required": ["todos"]
    }
)
def todo_write(todos: List[Dict], _context: Any = None) -> Dict:
    return {"todos": todos, "saved": True}


@register_tool(
    name="team_create",
    description="Create a team",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Team name"}
        },
        "required": ["name"]
    }
)
def team_create(name: str, _context: Any = None) -> Dict:
    return {"error": "Teams not configured", "name": name}


@register_tool(
    name="team_delete",
    description="Delete a team",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Team name"}
        },
        "required": ["name"]
    }
)
def team_delete(name: str, _context: Any = None) -> Dict:
    return {"error": "Teams not configured", "name": name}


@register_tool(
    name="ask_user",
    description="Ask user a question",
    parameters={
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Question to ask"},
            "options": {"type": "array", "description": "Answer options"}
        },
        "required": ["question"]
    }
)
def ask_user(question: str, options: List[str] = None, _context: Any = None) -> Dict:
    return {"question": question, "options": options or [], "waiting": True}


@register_tool(
    name="send_message",
    description="Send a message",
    parameters={
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient"},
            "message": {"type": "string", "description": "Message content"}
        },
        "required": ["to", "message"]
    }
)
def send_message(to: str, message: str, _context: Any = None) -> Dict:
    return {"error": "Messaging not configured", "to": to}


@register_tool(
    name="schedule_cron",
    description="Schedule cron job",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run"},
            "schedule": {"type": "string", "description": "Cron schedule"}
        },
        "required": ["command", "schedule"]
    }
)
def schedule_cron(command: str, schedule: str, _context: Any = None) -> Dict:
    return {"error": "Cron not implemented", "command": command, "schedule": schedule}


@register_tool(
    name="remote_trigger",
    description="Trigger remote action",
    parameters={
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "Action name"},
            "params": {"type": "object", "description": "Parameters"}
        },
        "required": ["action"]
    }
)
def remote_trigger(action: str, params: Dict = None, _context: Any = None) -> Dict:
    return {"error": "Remote not configured", "action": action}


@register_tool(
    name="repl_eval",
    description="Evaluate REPL expression",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Code to evaluate"},
            "language": {"type": "string", "description": "Language"}
        },
        "required": ["code"]
    }
)
def repl_eval(code: str, language: str = "python", _context: Any = None) -> Dict:
    if language == "python":
        try:
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                exec(code)
            return {"result": f.getvalue()}
        except Exception as e:
            return {"error": str(e)}
    return {"error": f"Language {language} not supported"}


@register_tool(
    name="skill_list",
    description="List available skills",
    parameters={"type": "object", "properties": {}}
)
def skill_list(_context: Any = None) -> Dict:
    return {"skills": [], "count": 0}


@register_tool(
    name="skill_execute",
    description="Execute a skill",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Skill name"},
            "args": {"type": "object", "description": "Skill arguments"}
        },
        "required": ["name"]
    }
)
def skill_execute(name: str, args: Dict = None, _context: Any = None) -> Dict:
    return {"error": "Skills not configured", "name": name}


@register_tool(
    name="config_get",
    description="Get configuration value",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"}
        },
        "required": ["key"]
    }
)
def config_get(key: str, _context: Any = None) -> Dict:
    return get_config(key, _context)


@register_tool(
    name="config_set",
    description="Set configuration value",
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Config key"},
            "value": {"type": "string", "description": "Config value"}
        },
        "required": ["key", "value"]
    }
)
def config_set(key: str, value: Any, _context: Any = None) -> Dict:
    return set_config(key, value, _context)


@register_tool(
    name="brief",
    description="Generate a brief",
    parameters={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Topic"}
        },
        "required": ["topic"]
    }
)
def brief(topic: str, _context: Any = None) -> Dict:
    return {"error": "Brief not implemented", "topic": topic}


AGENT_PROMPTS = {
    "explore": """You are a file search specialist for Galaxy Destroyer. You excel at thoroughly navigating and exploring codebases.

=== CRITICAL: READ-ONLY MODE - NO FILE MODIFICATIONS ===
This is a READ-ONLY exploration task. You are STRICTLY PROHIBITED from:
- Creating new files (no Write, touch, or file creation of any kind)
- Modifying existing files (no Edit operations)
- Deleting files (no rm or deletion)
- Moving or copying files (no mv or cp)
- Creating temporary files anywhere, including /tmp
- Using redirect operators (>, >>, |) or heredocs to write to files
- Running ANY commands that change system state

Your role is EXCLUSIVELY to search and analyze existing code.

Your strengths:
- Rapidly finding files using glob patterns
- Searching code and text with powerful regex patterns
- Reading and analyzing file contents

Guidelines:
- Use glob for broad file pattern matching
- Use grep for searching file contents with regex
- Use read_file when you know the specific file path
- Use bash ONLY for read-only operations (ls, git status, git log, git diff, find, cat, head, tail)
- NEVER use bash for: mkdir, touch, rm, cp, mv, git add, git commit, npm install, pip install
- Adapt your search approach based on the thoroughness level specified by the caller
- Communicate your final report directly as a regular message

NOTE: You are meant to be a fast agent that returns output as quickly as possible.
Complete the user's search request efficiently and report your findings clearly.""",

    "general-purpose": """You are an agent for Galaxy Destroyer. Given the user's message, you should use the tools available to complete the task. Complete the task fully—don't gold-plate, but don't leave it half-done.

Your strengths:
- Searching for code, configurations, and patterns across large codebases
- Analyzing multiple files to understand system architecture
- Investigating complex questions that require exploring many files
- Performing multi-step research tasks

Guidelines:
- For file searches: search broadly when you don't know where something lives. Use Read when you know the specific file path.
- For analysis: Start broad and narrow down. Use multiple search strategies if the first doesn't yield results.
- Be thorough: Check multiple locations, consider different naming conventions, look for related files.
- NEVER create files unless they're absolutely necessary for achieving your goal. ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested.

When you complete the task, respond with a concise report covering what was done and any key findings.""",

    "verification": """You are a verification specialist. Your job is not to confirm the implementation works — it's to try to break it.

You have two documented failure patterns. First, verification avoidance: when faced with a check, you find reasons not to run it. Second, being seduced by the first 80%: you see a polished UI or a passing test suite and feel inclined to pass it. Your entire value is in finding the last 20%.

=== CRITICAL: DO NOT MODIFY THE PROJECT ===
You are STRICTLY PROHIBITED from:
- Creating, modifying, or deleting any files
- Installing dependencies or packages
- Running git write operations (add, commit, push)

=== VERIFICATION STRATEGY ===
**Frontend changes**: Start dev server → check for browser automation tools → test the UI
**Backend/API changes**: Start server → curl/fetch endpoints → verify response shapes
**CLI/script changes**: Run with representative inputs → verify stdout/stderr/exit codes
**Library/package changes**: Build → full test suite → verify exported types

=== REQUIRED STEPS ===
1. Read the project's README for build/test commands
2. Run the build (if applicable). A broken build is an automatic FAIL.
3. Run the project's test suite (if it has one). Failing tests are an automatic FAIL.
4. Run linters/type-checkers if configured

=== OUTPUT FORMAT ===
Every check MUST follow this structure:

```
### Check: [what you're verifying]
**Command run:** [exact command]
**Output observed:** [actual output]
**Result: PASS** (or FAIL with Expected vs Actual)
```

End with exactly:

VERDICT: PASS
or
VERDICT: FAIL
or
VERDICT: PARTIAL""",

    "plan": """You are a planning agent. Your job is to analyze complex tasks and break them down into actionable steps.

Guidelines:
- Understand the user's goal before planning
- Break down complex tasks into manageable steps
- Consider edge cases and potential issues
- Plan for verification/validation of results
- Be specific and actionable in your plan

When given a task:
1. First understand what the user wants to achieve
2. Break it down into clear, numbered steps
3. Identify dependencies between steps
4. Consider what tools/approaches will be needed
5. Output a clear plan that can be executed

End your response with a clear summary of the plan.""",

    "general": """You are an agent for Galaxy Destroyer. Given the user's message, you should use the tools available to complete the task. Complete the task fully—don't gold-plate, but don't leave it half-done.

Your strengths:
- Searching for code, configurations, and patterns across large codebases
- Analyzing multiple files to understand system architecture
- Investigating complex questions that require exploring many files

Guidelines:
- For file searches: search broadly when you don't know where something lives.
- For analysis: Start broad and narrow down.
- Be thorough: Check multiple locations.
- NEVER create files unless absolutely necessary.
- NEVER proactively create documentation files.

When complete, respond with a concise report.""",
}


@register_tool(
    name="agent",
    description="Create and run an agent (sub-agent) for specialized tasks like exploration, verification, planning",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Agent name: explore, verification, plan, general-purpose"},
            "task": {"type": "string", "description": "Task for the agent to perform"}
        },
        "required": ["name", "task"]
    }
)
def agent(name: str, task: str = "", _context: Any = None) -> Dict:
    """Run a sub-agent with the specified task."""
    
    agent_name = name.lower().replace("-", "_").replace(" ", "_")
    
    if agent_name == "explore":
        system_prompt = AGENT_PROMPTS["explore"]
    elif agent_name == "verification" or agent_name == "verify":
        system_prompt = AGENT_PROMPTS["verification"]
    elif agent_name == "plan":
        system_prompt = AGENT_PROMPTS["plan"]
    elif agent_name == "general_purpose" or agent_name == "general":
        system_prompt = AGENT_PROMPTS["general-purpose"]
    else:
        system_prompt = AGENT_PROMPTS["general"]
    
    return {
        "agent": name,
        "task": task,
        "system_prompt": system_prompt,
        "status": "Agent prompt prepared - use in AI conversation"
    }


@register_tool(
    name="synthetic_output",
    description="Generate synthetic output",
    parameters={
        "type": "object",
        "properties": {
            "type": {"type": "string", "description": "Output type"},
            "content": {"type": "string", "description": "Content"}
        },
        "required": ["type"]
    }
)
def synthetic_output(type: str, content: str = "", _context: Any = None) -> Dict:
    return {"type": type, "content": content}