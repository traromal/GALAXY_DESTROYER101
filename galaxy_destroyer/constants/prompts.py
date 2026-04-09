"""System prompt builder - builds AI system prompts like Claude Code"""

import os
import platform
from typing import List, Optional, Set

from .system import (
    CLI_SYSPROMPT_PREFIX,
    SYSTEM_PROMPT_DYNAMIC_BOUNDARY,
    MODEL_IDS,
    get_shell_info_line,
    get_os_version,
    get_cwd,
    get_session_date,
    get_knowledge_cutoff,
    TOOLS_SECTION,
    ACTIONS_SECTION,
    DOING_TASKS_SECTION,
    TONE_SECTION,
    OUTPUT_EFFICIENCY_SECTION,
    SYSTEM_REMINDERS_SECTION,
    HOOKS_SECTION,
)


def prepend_bullets(items: List[str]) -> List[str]:
    return [f"  - {item}" for item in items]


def get_intro_section() -> str:
    return f"""{CLI_SYSPROMPT_PREFIX}

Cyber Risk Instruction: You are an AI coding assistant. Do not generate malicious code, exploits, or harmful content. Prioritize security and user safety in all responses."""


def get_environment_section(
    model_id: str,
    additional_dirs: Optional[List[str]] = None,
    is_git: bool = False,
) -> str:
    cutoff = get_knowledge_cutoff(model_id)
    cutoff_msg = f"\n\nAssistant knowledge cutoff is {cutoff}." if cutoff else ""

    additional_dirs_info = ""
    if additional_dirs:
        additional_dirs_info = (
            f"\nAdditional working directories: {', '.join(additional_dirs)}"
        )

    return f"""# Environment

You have been invoked in the following environment:
{
        chr(10).join(
            prepend_bullets(
                [
                    f"Primary working directory: {get_cwd()}",
                    f"Is a git repository: {'Yes' if is_git else 'No'}",
                    f"{additional_dirs_info}" if additional_dirs_info else None,
                    f"Platform: {platform.system().lower()}",
                    get_shell_info_line(),
                    f"OS Version: {get_os_version()}",
                    f"Date: {get_session_date()}",
                    f"You are powered by the model {model_id}.",
                    cutoff_msg,
                ]
            )
        )
    }"""


def get_language_section(language: Optional[str] = None) -> Optional[str]:
    if not language:
        return None
    return f"""# Language

Always respond in {language}. Use {language} for all explanations, comments, and communications."""


def get_system_prompt(
    model_id: str,
    enabled_tools: Set[str],
    is_git: bool = False,
    additional_dirs: Optional[List[str]] = None,
    language: Optional[str] = None,
    include_dynamic: bool = True,
) -> List[str]:
    sections = [
        get_intro_section(),
        SYSTEM_REMINDERS_SECTION,
        DOING_TASKS_SECTION,
        ACTIONS_SECTION,
        TOOLS_SECTION,
        TONE_SECTION,
        OUTPUT_EFFICIENCY_SECTION,
    ]

    if include_dynamic:
        sections.append(SYSTEM_PROMPT_DYNAMIC_BOUNDARY)

    sections.extend(
        [
            get_environment_section(model_id, additional_dirs, is_git),
        ]
    )

    if language:
        lang_section = get_language_section(language)
        if lang_section:
            sections.append(lang_section)

    return sections


def get_simple_system_prompt(model_id: str) -> str:
    return f"""{CLI_SYSPROMPT_PREFIX}

CWD: {get_cwd()}
Date: {get_session_date()}

Model: {model_id}"""


def get_agent_prompt(model_id: str) -> str:
    return f"""{CLI_SYSPROMPT_PREFIX}

Given the user's message, use the tools available to complete the task.

Environment:
- Working directory: {get_cwd()}
- Date: {get_session_date()}
- Model: {model_id}

Guidelines:
- Use absolute file paths (cwd resets between bash calls)
- Complete tasks fully - don't gold-plate, don't leave half-done
- Be concise in reporting results
- Avoid emojis
- Don't use colons before tool calls"""
