"""Constants package"""

from .system import (
    CLI_SYSPROMPT_PREFIX,
    SYSTEM_PROMPT_DYNAMIC_BOUNDARY,
    MODEL_IDS,
    TOOLS_SECTION,
    ACTIONS_SECTION,
    DOING_TASKS_SECTION,
    TONE_SECTION,
    OUTPUT_EFFICIENCY_SECTION,
    SYSTEM_REMINDERS_SECTION,
    HOOKS_SECTION,
)
from .prompts import (
    get_system_prompt,
    get_simple_system_prompt,
    get_agent_prompt,
    get_environment_section,
)

__all__ = [
    "CLI_SYSPROMPT_PREFIX",
    "SYSTEM_PROMPT_DYNAMIC_BOUNDARY",
    "MODEL_IDS",
    "TOOLS_SECTION",
    "ACTIONS_SECTION",
    "DOING_TASKS_SECTION",
    "TONE_SECTION",
    "OUTPUT_EFFICIENCY_SECTION",
    "SYSTEM_REMINDERS_SECTION",
    "HOOKS_SECTION",
    "get_system_prompt",
    "get_simple_system_prompt",
    "get_agent_prompt",
    "get_environment_section",
]
