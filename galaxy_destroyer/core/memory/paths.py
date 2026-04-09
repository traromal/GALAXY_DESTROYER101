import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from galaxy_destroyer.utils.path import sanitize_path


ENTRYPOINT_NAME = "MEMORY.md"
MAX_ENTRYPOINT_LINES = 200
MAX_ENTRYPOINT_BYTES = 25_000


@lru_cache(maxsize=1)
def get_config_home() -> str:
    return os.path.expanduser("~/.galaxy_destroyer")


def get_memory_base_dir() -> str:
    remote_dir = os.environ.get("GALAXY_CODE_REMOTE_MEMORY_DIR")
    if remote_dir:
        return remote_dir
    return get_config_home()


def _validate_memory_path(raw: str | None, expand_tilde: bool = True) -> Optional[str]:
    if not raw:
        return None

    candidate = raw

    if expand_tilde and (candidate.startswith("~/") or candidate.startswith("~\\")):
        rest = candidate[2:]
        if not rest or rest in (".", ".."):
            return None
        candidate = os.path.expanduser(candidate)

    normalized = os.path.normpath(candidate).rstrip("/\\")

    if not os.path.isabs(normalized):
        return None
    if len(normalized) < 3:
        return None
    if normalized.replace("\\", "").replace("/", "").__len__() < 2:
        return None

    sep = os.sep
    return normalized + sep


@lru_cache(maxsize=1)
def get_project_root() -> str:
    return os.getcwd()


@lru_cache(maxsize=1)
def _find_git_root(cwd: str) -> Optional[str]:
    current = Path(cwd)
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent
    return None


@lru_cache(maxsize=1)
def get_auto_mem_base() -> str:
    git_root = _find_git_root(get_project_root())
    if git_root:
        return git_root
    return get_project_root()


@lru_cache(maxsize=1)
def get_auto_mem_path() -> str:
    override = os.environ.get("GALAXY_COWORK_MEMORY_PATH_OVERRIDE")
    if override:
        validated = _validate_memory_path(override, expand_tilde=False)
        if validated:
            return validated

    base = get_memory_base_dir()
    projects_dir = os.path.join(base, "projects")
    sanitized = sanitize_path(get_auto_mem_base())

    sep = os.sep
    return os.path.join(projects_dir, sanitized, "memory") + sep


@lru_cache(maxsize=1)
def get_auto_mem_entrypoint() -> str:
    return os.path.join(get_auto_mem_path(), ENTRYPOINT_NAME)


def get_daily_log_path(date: Optional[str] = None) -> str:
    if date is None:
        from datetime import datetime

        date = datetime.now().strftime("%Y-%m-%d")

    year = date[:4]
    month = date[5:7]

    log_dir = os.path.join(get_auto_mem_path(), "logs", year, month)
    return os.path.join(log_dir, f"{date}.md")


def is_auto_mem_path(absolute_path: str) -> bool:
    normalized = os.path.normpath(absolute_path)
    mem_path = get_auto_mem_path()
    return normalized.startswith(mem_path)


def is_auto_memory_enabled() -> bool:
    if os.environ.get("GALAXY_CODE_DISABLE_AUTO_MEMORY", "").lower() in ("1", "true"):
        return False

    if os.environ.get("GALAXY_CODE_SIMPLE", "").lower() in ("1", "true"):
        return False

    if os.environ.get("GALAXY_CODE_REMOTE") and not os.environ.get(
        "GALAXY_CODE_REMOTE_MEMORY_DIR"
    ):
        return False

    return True
