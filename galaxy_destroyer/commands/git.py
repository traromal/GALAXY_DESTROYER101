"""Git commands - commit, diff, status, branch, etc."""

import subprocess
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from . import register_command, CommandCategory
from galaxy_destroyer.core.render import style


def _run_git(args: List[str], cwd: Optional[str] = None) -> Dict:
    try:
        result = subprocess.run(
            ["git"] + args, cwd=cwd or os.getcwd(), capture_output=True, text=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except FileNotFoundError:
        return {"error": "Git not installed", "returncode": -1}
    except Exception as e:
        return {"error": str(e), "returncode": -1}


def _is_git_repo(cwd: Optional[str] = None) -> bool:
    result = _run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    return result.get("returncode", -1) == 0


def _get_cwd(app) -> str:
    return app.context.cwd if app and hasattr(app, "context") else os.getcwd()


@register_command(
    name="git",
    description="Git repository information",
    category=CommandCategory.GIT,
    usage="git [subcommand]",
    examples=["git status", "git log -5"],
)
def cmd_git(args: List[str] = None, app=None):
    if not args:
        cwd = _get_cwd(app)
        if _is_git_repo(cwd):
            return style("Git repository detected", color="green")
        return style("Not a git repository", color="red")

    result = _run_git(args, _get_cwd(app))
    if result.get("returncode", -1) == 0:
        return result.get("stdout", "")
    return f"Error: {result.get('stderr', result.get('error', 'Unknown error'))}"


@register_command(
    name="status",
    description="Show working tree status",
    category=CommandCategory.GIT,
    aliases=["git_status"],
)
def cmd_status(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    result = _run_git(["status", "--porcelain"], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('error', '')}"

    lines = result.get("stdout", "").strip().split("\n")
    if not lines or lines == [""]:
        return style("Working tree is clean", color="green")

    output = [style("Changed files:", bold=True)]
    for line in lines:
        if line:
            status = line[:2]
            filename = line[3:]
            color = "red" if status[0] != " " or status[1] != " " else "yellow"
            output.append(f"  {style(status, color=color)} {filename}")

    return "\n".join(output)


@register_command(
    name="commit",
    description="Create a commit",
    category=CommandCategory.GIT,
    usage="commit <message>",
    examples=["commit Fix bug in login"],
)
def cmd_commit(args: List[str] = None, app=None):
    if not args:
        return style("Usage: commit <message>", color="yellow")

    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    message = " ".join(args)

    result = _run_git(["add", "-A"], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error staging: {result.get('error', '')}"

    result = _run_git(["commit", "-m", message], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style(f"Committed: {message}", color="green")


@register_command(
    name="branch",
    description="List, create, or delete branches",
    category=CommandCategory.GIT,
    usage="branch [name]",
    examples=["branch", "branch feature-login"],
)
def cmd_branch(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    if not args:
        result = _run_git(["branch", "-v"], cwd)
        if result.get("returncode", -1) != 0:
            return f"Error: {result.get('error', '')}"

        lines = result.get("stdout", "").strip().split("\n")
        output = []
        for line in lines:
            if line.startswith("*"):
                output.append(style(line, color="green", bold=True))
            else:
                output.append(line)
        return "\n".join(output)

    name = args[0]
    if len(args) > 1 and args[1] == "-d":
        result = _run_git(["branch", "-d", name], cwd)
    else:
        result = _run_git(["branch", name], cwd)

    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style(f"Created branch: {name}", color="green")


@register_command(
    name="checkout",
    description="Switch branches or restore files",
    category=CommandCategory.GIT,
    usage="checkout <branch|file>",
    examples=["checkout main", "checkout -- file.txt"],
)
def cmd_checkout(args: List[str] = None, app=None):
    if not args:
        return style("Usage: checkout <branch|file>", color="yellow")

    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    result = _run_git(["checkout", args[0]], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style(f"Switched to: {args[0]}", color="green")


@register_command(
    name="log",
    description="Show commit logs",
    category=CommandCategory.GIT,
    usage="log [limit]",
    examples=["log", "log -10"],
)
def cmd_log(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    limit = "-n10"
    if args and args[0].isdigit():
        limit = f"-n{args[0]}"

    result = _run_git(["log", limit, "--oneline", "--graph", "--decorate"], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('error', '')}"

    return result.get("stdout", "")


@register_command(
    name="diff",
    description="Show changes",
    category=CommandCategory.GIT,
    usage="diff [file]",
    examples=["diff", "diff src/main.py"],
)
def cmd_diff(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    cmd = ["diff", "--color=never"]
    if args:
        cmd.append(args[0])

    result = _run_git(cmd, cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('error', '')}"

    return result.get("stdout", "(no changes)")


@register_command(
    name="push",
    description="Push commits to remote",
    category=CommandCategory.GIT,
    usage="push [remote] [branch]",
    examples=["push origin main"],
)
def cmd_push(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    cmd = ["push"]
    if args:
        cmd.extend(args)

    result = _run_git(cmd, cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style("Pushed successfully", color="green")


@register_command(
    name="pull",
    description="Fetch and integrate with remote",
    category=CommandCategory.GIT,
    usage="pull [remote] [branch]",
)
def cmd_pull(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    cmd = ["pull"]
    if args:
        cmd.extend(args)

    result = _run_git(cmd, cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style("Pulled successfully", color="green")


@register_command(
    name="fetch",
    description="Download objects from remote",
    category=CommandCategory.GIT,
    usage="fetch [remote]",
)
def cmd_fetch(args: List[str] = None, app=None):
    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    cmd = ["fetch"]
    if args:
        cmd.append(args[0])

    result = _run_git(cmd, cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style("Fetched successfully", color="green")


@register_command(
    name="merge",
    description="Join two or more branches",
    category=CommandCategory.GIT,
    usage="merge <branch>",
)
def cmd_merge(args: List[str] = None, app=None):
    if not args:
        return style("Usage: merge <branch>", color="yellow")

    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    result = _run_git(["merge", args[0]], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style(f"Merged {args[0]}", color="green")


@register_command(
    name="rebase",
    description="Reapply commits on top of another base",
    category=CommandCategory.GIT,
    usage="rebase <branch>",
)
def cmd_rebase(args: List[str] = None, app=None):
    if not args:
        return style("Usage: rebase <branch>", color="yellow")

    cwd = _get_cwd(app)
    if not _is_git_repo(cwd):
        return style("Not a git repository", color="red")

    result = _run_git(["rebase", args[0]], cwd)
    if result.get("returncode", -1) != 0:
        return f"Error: {result.get('stderr', result.get('error', ''))}"

    return style(f"Rebased onto {args[0]}", color="green")
