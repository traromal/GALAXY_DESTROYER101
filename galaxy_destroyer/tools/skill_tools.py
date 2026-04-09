"""Skill tools for Galaxy Destroyer"""

from typing import Any, Dict

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter
from galaxy_destroyer.services.skills import list_skills, get_skill, execute_skill


@register_tool(
    name="skill_list",
    description="List all available skills",
    category=ToolCategory.SKILLS,
)
def skill_list(_context: Any = None) -> Dict:
    return list_skills()


@register_tool(
    name="skill_execute",
    description="Execute a skill",
    category=ToolCategory.SKILLS,
    parameters=[
        ToolParameter(name="name", description="Skill name", required=True),
    ],
)
def skill_execute(name: str, _context: Any = None, **kwargs) -> Dict:
    result = execute_skill(name, kwargs)
    if "error" in result:
        return result

    return {
        "skill": result["name"],
        "prompt": result["content"],
        "shell": result.get("shell"),
    }


@register_tool(
    name="skill_info",
    description="Get information about a skill",
    category=ToolCategory.SKILLS,
    parameters=[
        ToolParameter(name="name", description="Skill name", required=True),
    ],
)
def skill_info(name: str, _context: Any = None) -> Dict:
    skill = get_skill(name)

    if not skill:
        return {"error": f"Skill not found: {name}"}

    return {
        "name": skill.name,
        "description": skill.description,
        "source": skill.source,
        "path": skill.path,
        "tags": skill.tags,
        "shell": skill.shell,
    }
