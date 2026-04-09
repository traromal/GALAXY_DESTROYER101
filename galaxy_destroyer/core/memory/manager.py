import os
from dataclasses import dataclass
from typing import Optional

from .paths import (
    ENTRYPOINT_NAME,
    MAX_ENTRYPOINT_BYTES,
    MAX_ENTRYPOINT_LINES,
    get_auto_mem_entrypoint,
    get_auto_mem_path,
    is_auto_memory_enabled,
)
from .types import (
    MEMORY_FRONTMATTER_EXAMPLE,
    TRUSTING_RECALL_SECTION,
    TYPES_SECTION_INDIVIDUAL,
    WHAT_NOT_TO_SAVE_SECTION,
    WHEN_TO_ACCESS_SECTION,
)


@dataclass
class TruncationResult:
    content: str
    line_count: int
    byte_count: int
    was_line_truncated: bool
    was_byte_truncated: bool


def truncate_entrypoint_content(raw: str) -> TruncationResult:
    trimmed = raw.strip()
    content_lines = trimmed.split("\n")
    line_count = len(content_lines)
    byte_count = len(trimmed.encode("utf-8"))

    was_line_truncated = line_count > MAX_ENTRYPOINT_LINES
    was_byte_truncated = byte_count > MAX_ENTRYPOINT_BYTES

    if not was_line_truncated and not was_byte_truncated:
        return TruncationResult(
            content=trimmed,
            line_count=line_count,
            byte_count=byte_count,
            was_line_truncated=False,
            was_byte_truncated=False,
        )

    truncated = trimmed
    if was_line_truncated:
        truncated = "\n".join(content_lines[:MAX_ENTRYPOINT_LINES])

    truncated_bytes = truncated.encode("utf-8")
    if len(truncated_bytes) > MAX_ENTRYPOINT_BYTES:
        cut_at = MAX_ENTRYPOINT_BYTES
        for i in range(len(truncated) - 1, -1, -1):
            if truncated[i] == "\n":
                cut_at = i
                break
        truncated = truncated[:cut_at]

    reason_parts = []
    if was_byte_truncated:
        from utils.format import format_file_size

        reason_parts.append(
            f"{format_file_size(byte_count)} (limit: {format_file_size(MAX_ENTRYPOINT_BYTES)})"
        )
    if was_line_truncated:
        reason_parts.append(f"{line_count} lines (limit: {MAX_ENTRYPOINT_LINES})")
    reason = " and ".join(reason_parts)

    truncated += f"\n\n> WARNING: {ENTRYPOINT_NAME} is {reason}. Only part was loaded."

    return TruncationResult(
        content=truncated,
        line_count=line_count,
        byte_count=byte_count,
        was_line_truncated=was_line_truncated,
        was_byte_truncated=was_byte_truncated,
    )


def ensure_memory_dir_exists() -> None:
    mem_dir = get_auto_mem_path()
    os.makedirs(mem_dir, exist_ok=True)


def build_memory_prompt(extra_guidelines: Optional[list[str]] = None) -> str:
    if not is_auto_memory_enabled():
        return ""

    mem_dir = get_auto_mem_path()
    ensure_memory_dir_exists()

    lines = [
        f"# auto memory",
        "",
        f"You have a persistent, file-based memory system at `{mem_dir}`.",
        "",
        "You should build up this memory system over time so that future conversations can have a complete picture of who the user is, how they'd like to collaborate with you, what behaviors to avoid or repeat.",
        "",
        "If the user explicitly asks you to remember something, save it immediately as whichever type fits best.",
        "",
        *TYPES_SECTION_INDIVIDUAL,
        "",
        *WHAT_NOT_TO_SAVE_SECTION,
        "",
        "## How to save memories",
        "",
        "**Step 1** — write the memory to its own file using this format:",
        "",
        *MEMORY_FRONTMATTER_EXAMPLE,
        "",
        f"**Step 2** — add a pointer to `{ENTRYPOINT_NAME}`: `- [Title](file.md) — one-line hook`",
        "",
        f"- `{ENTRYPOINT_NAME}` is always loaded into context — lines after {MAX_ENTRYPOINT_LINES} will be truncated",
        "- Keep the name, description, and type fields up-to-date",
        "- Do not write duplicate memories. Check for existing memories first.",
        "",
        *WHEN_TO_ACCESS_SECTION,
        "",
        *TRUSTING_RECALL_SECTION,
    ]

    if extra_guidelines:
        lines.extend(["", *extra_guidelines])

    lines.append("")
    lines.append(f"## {ENTRYPOINT_NAME}")
    lines.append("")

    entrypoint = get_auto_mem_entrypoint()
    if os.path.exists(entrypoint):
        with open(entrypoint, "r", encoding="utf-8") as f:
            content = f.read()

        if content.strip():
            truncated = truncate_entrypoint_content(content)
            lines.append(truncated.content)
        else:
            lines.append(f"Your {ENTRYPOINT_NAME} is currently empty.")
    else:
        lines.append(f"Your {ENTRYPOINT_NAME} is currently empty.")

    return "\n".join(lines)


def read_memory_entrypoint() -> Optional[str]:
    entrypoint = get_auto_mem_entrypoint()
    if os.path.exists(entrypoint):
        with open(entrypoint, "r", encoding="utf-8") as f:
            return f.read()
    return None


def write_memory_entrypoint(content: str) -> None:
    ensure_memory_dir_exists()
    entrypoint = get_auto_mem_entrypoint()
    with open(entrypoint, "w", encoding="utf-8") as f:
        f.write(content)
