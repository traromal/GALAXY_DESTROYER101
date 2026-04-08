# Galaxy Destroyer

<p align="center">
  <img src="https://img.shields.io/pypi/v/galaxy-destroyer" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/l/galaxy-destroyer" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/galaxy-destroyer" alt="Python Versions">
</p>

AI-powered terminal assistant - A Python implementation inspired by Claude Code.

## Features

- 🤖 **AI Integration** - Connect to Claude API for intelligent assistance
- 🛠️ **52 Built-in Tools** - File operations, git, search, web, and more
- 📁 **File Operations** - Read, write, edit, list, search files
- 🔍 **Search** - Grep, glob, find files by pattern
- 📦 **Git** - Status, commit, branch, diff, push, pull
- 🌐 **Web** - Fetch pages, search the web
- 📋 **Task Management** - Create, update, list tasks
- 🔌 **MCP Support** - Model Context Protocol integration
- 📝 **Vim Mode** - Full vim-style text editing
- 🎨 **Beautiful TUI** - Rich terminal UI with colors and borders

## Installation

### From PyPI (coming soon)
```bash
pip install galaxy-destroyer
```

### From GitHub
```bash
git clone https://github.com/galaxydestroyer/galaxy-destroyer.git
cd galaxy-destroyer
pip install -e .
```

## Quick Start

### Interactive Mode
```bash
galaxy
# or
python -m galaxy_destroyer.cli
```

### Quick Ask
```bash
galaxy ask "Hello, how are you?"
```

### Run Commands
```bash
galaxy run "ls -la"
```

### Use Tools Directly
```bash
galaxy tool read_file path=README.md
galaxy tool git_status
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

## Commands

| Command | Description |
|---------|-------------|
| `help` | Show help |
| `ask <prompt>` | Ask AI |
| `tool <name>` | Run tool |
| `tools` | List tools |
| `git` | Git commands |
| `cd` | Change directory |
| `ls` | List files |
| `cat` | Read file |
| `exit` | Exit |

## Available Tools

- **File**: read_file, write_file, edit_file, delete_file, move_file, list_directory, glob, file_info
- **Search**: search_files, grep, glob_files
- **Git**: git_status, git_log, git_diff
- **Web**: web_fetch, web_search
- **MCP**: mcp_list_resources, mcp_read_resource, mcp_call_tool
- **Tasks**: task_create, task_get, task_list, task_update, task_stop, todo_write
- **Config**: config_get, config_set, get_config, set_config
- **System**: bash, run_shell, get_env, repl_eval
- **And more**: agent, ask_user, enter_plan_mode, exit_plan_mode, skill_execute, etc.

## Configuration

Config is stored in `~/.galaxy_destroyer_config.json`

```json
{
  "model": "claude-opus-4-5-20251114",
  "color": true,
  "stream": true
}
```

## Development

```bash
# Clone repository
git clone https://github.com/galaxydestroyer/galaxy-destroyer.git
cd galaxy-destroyer

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
black galaxy_destroyer/

# Type checking
mypy galaxy_destroyer/
```

## License

MIT License - See LICENSE file

## Contributing

Contributions welcome! Please open an issue or submit a PR.

---

<p align="center">Built with ❤️ by the Galaxy Team</p>