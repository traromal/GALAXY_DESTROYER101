from typing import Literal, TypedDict


MEMORY_TYPES = ["user", "feedback", "project", "reference"]

MemoryType = Literal["user", "feedback", "project", "reference"]


def parse_memory_type(raw: str | None) -> MemoryType | None:
    if not raw:
        return None
    if raw in MEMORY_TYPES:
        return raw  # type: ignore
    return None


MEMORY_FRONTMATTER_TEMPLATE = """---
name: {name}
description: {description}
type: {type}
---

{content}
"""


TYPES_SECTION_INDIVIDUAL = [
    "## Types of memory",
    "",
    "There are several discrete types of memory that you can store in your memory system:",
    "",
    "<types>",
    "<type>",
    "    <name>user</name>",
    "    <description>Contain information about the user's role, goals, responsibilities, and knowledge. Great user memories help you tailor your future behavior to the user's preferences and perspective.</description>",
    "    <when_to_save>When you learn any details about the user's role, preferences, responsibilities, or knowledge</when_to_save>",
    "    <how_to_use>When your work should be informed by the user's profile or perspective.</how_to_use>",
    "    <examples>",
    "    user: I'm a data scientist investigating what logging we have in place",
    "    assistant: [saves user memory: user is a data scientist, currently focused on observability/logging]",
    "",
    "    user: I've been writing Go for ten years but this is my first time touching the React side of this repo",
    "    assistant: [saves user memory: deep Go expertise, new to React and this project's frontend]</description>",
    "    </examples>",
    "</type>",
    "<type>",
    "    <name>feedback</name>",
    "    <description>Guidance the user has given you about how to approach work — both what to avoid and what to keep doing.</description>",
    "    <when_to_save>Any time the user corrects your approach or confirms a non-obvious approach worked.</when_to_save>",
    "    <how_to_use>Let these memories guide your behavior so that the user does not need to offer the same guidance twice.</how_to_use>",
    "    <body_structure>Lead with the rule itself, then a **Why:** line and a **How to apply:** line.</body_structure>",
    "    <examples>",
    "    user: don't mock the database in these tests — we got burned last quarter",
    "    assistant: [saves feedback memory: integration tests must hit a real database, not mocks]",
    "",
    "    user: stop summarizing what you just did at the end of every response",
    "    assistant: [saves feedback memory: this user wants terse responses with no trailing summaries]",
    "    </examples>",
    "</type>",
    "<type>",
    "    <name>project</name>",
    "    <description>Information that you learn about ongoing work, goals, initiatives, bugs, or incidents within the project.</description>",
    "    <when_to_save>When you learn who is doing what, why, or by when.</when_to_save>",
    "    <how_to_use>Use these memories to understand the broader context behind the user's requests.</how_to_use>",
    "    <examples>",
    "    user: we're freezing all non-critical merges after Thursday",
    "    assistant: [saves project memory: merge freeze begins 2026-04-09 for mobile release cut]",
    "    </examples>",
    "</type>",
    "<type>",
    "    <name>reference</name>",
    "    <description>Stores pointers to where information can be found in external systems.</description>",
    "    <when_to_save>When you learn about resources in external systems and their purpose.</when_to_save>",
    "    <how_to_use>When the user references an external system or information that may be in an external system.</how_to_use>",
    "    <examples>",
    "    user: check the Linear project INGEST for context on these tickets",
    "    assistant: [saves reference memory: pipeline bugs are tracked in Linear project INGEST]",
    "    </examples>",
    "</type>",
    "</types>",
    "",
]


WHAT_NOT_TO_SAVE_SECTION = [
    "## What NOT to save in memory",
    "",
    "- Code patterns, conventions, architecture, file paths, or project structure — these can be derived by reading the current project state.",
    "- Git history, recent changes, or who-changed-what — `git log` / `git blame` are authoritative.",
    "- Debugging solutions or fix recipes — the fix is in the code; the commit message has the context.",
    "- Anything already documented in CLAUDE.md files.",
    "- Ephemeral task details: in-progress work, temporary state, current conversation context.",
    "",
    "These exclusions apply even when the user explicitly asks you to save.",
]


WHEN_TO_ACCESS_SECTION = [
    "## When to access memories",
    "- When memories seem relevant, or the user references prior-conversation work.",
    "- You MUST access memory when the user explicitly asks you to check, recall, or remember.",
    "- If the user says to *ignore* or *not use* memory: proceed as if MEMORY.md were empty.",
    "- Memory records can become stale over time. Verify that the memory is still correct before acting on it.",
]


TRUSTING_RECALL_SECTION = [
    "## Before recommending from memory",
    "",
    "A memory that names a specific function, file, or flag is a claim that it existed *when the memory was written*. Before recommending it:",
    "",
    "- If the memory names a file path: check the file exists.",
    "- If the memory names a function or flag: grep for it.",
    "- If the user is about to act on your recommendation, verify first.",
    "",
    '"The memory says X exists" is not the same as "X exists now."',
]


MEMORY_FRONTMATTER_EXAMPLE = [
    "```markdown",
    "---",
    "name: {{memory name}}",
    "description: {{one-line description}}",
    f"type: {{{', '.join(MEMORY_TYPES)}}}",
    "---",
    "",
    "{{memory content — for feedback/project types, structure as: rule/fact, then **Why:** and **How to apply:** lines}}",
    "```",
]
