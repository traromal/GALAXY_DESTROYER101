import asyncio
import subprocess
from dataclasses import dataclass
from typing import Optional


MAX_STATUS_CHARS = 2000


@dataclass
class GitStatus:
    branch: str
    main_branch: str
    status: str
    recent_log: str
    user_name: Optional[str] = None


def _run_git_command(
    args: list[str], cwd: Optional[str] = None
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, "", str(e)


async def get_git_status() -> Optional[GitStatus]:
    try:
        code, _is_git, _ = _run_git_command(["rev-parse", "--is-inside-work-tree"])
        if code != 0:
            return None

        code, branch, _ = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch.strip() if code == 0 else "unknown"

        code, main_branch, _ = _run_git_command(
            ["rev-parse", "--abbrev-ref", "origin/HEAD"]
        )
        if code != 0:
            main_branch = "main"
        else:
            main_branch = main_branch.replace("origin/", "").strip()

        code, status, _ = _run_git_command(["--no-optional-locks", "status", "--short"])
        status = status.strip() if code == 0 else ""

        code, log, _ = _run_git_command(
            ["--no-optional-locks", "log", "--oneline", "-n", "5"]
        )
        log = log.strip() if code == 0 else ""

        code, user_name, _ = _run_git_command(["config", "user.name"])
        user_name = user_name.strip() if code == 0 else None

        return GitStatus(
            branch=branch,
            main_branch=main_branch,
            status=status or "(clean)",
            recent_log=log,
            user_name=user_name,
        )
    except Exception:
        return None


def build_git_context(git_status: Optional[GitStatus]) -> str:
    if not git_status:
        return ""

    truncated_status = git_status.status
    if len(truncated_status) > MAX_STATUS_CHARS:
        truncated_status = (
            truncated_status[:MAX_STATUS_CHARS]
            + "\n... (truncated. Run 'git status' for full output)"
        )

    lines = [
        "This is the git status at the start of the conversation.",
        f"Current branch: {git_status.branch}",
        f"Main branch (for PRs): {git_status.main_branch}",
    ]

    if git_status.user_name:
        lines.append(f"Git user: {git_status.user_name}")

    lines.extend(
        [
            f"Status:\n{truncated_status}",
            f"Recent commits:\n{git_status.recent_log}",
        ]
    )

    return "\n\n".join(lines)


async def get_git_context() -> dict[str, str]:
    git_status = await get_git_status()
    if not git_status:
        return {}

    context = build_git_context(git_status)
    if context:
        return {"gitStatus": context}
    return {}
