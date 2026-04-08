"""Skills system - load and execute skills from markdown files"""

import os
import re
import glob
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class Skill:
    name: str
    description: str
    content: str
    source: str
    path: str
    tags: List[str] = None
    shell: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith("---"):
        return {}, content
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter = {}
    yaml_content = parts[1]
    
    for line in yaml_content.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            frontmatter[key] = value
    
    return frontmatter, parts[2].strip()


def load_skill_from_file(filepath: str) -> Optional[Skill]:
    """Load a skill from a markdown file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        frontmatter, body = parse_frontmatter(content)
        
        name = frontmatter.get("name", os.path.splitext(os.path.basename(filepath))[0])
        description = frontmatter.get("description", "")
        shell = frontmatter.get("shell", None)
        tags_str = frontmatter.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
        
        return Skill(
            name=name,
            description=description,
            content=body,
            source="file",
            path=filepath,
            tags=tags,
            shell=shell,
        )
    except Exception:
        return None


def load_skills_from_directory(directory: str) -> List[Skill]:
    """Load all skills from a directory"""
    skills = []
    
    if not os.path.isdir(directory):
        return skills
    
    for filepath in glob.glob(os.path.join(directory, "**/*.md"), recursive=True):
        skill = load_skill_from_file(filepath)
        if skill:
            skills.append(skill)
    
    return skills


def get_default_skills_directories() -> List[str]:
    """Get default directories to search for skills"""
    dirs = []
    
    home = os.path.expanduser("~")
    
    global_skills_dir = os.path.join(home, ".claude", "skills")
    if os.path.isdir(global_skills_dir):
        dirs.append(global_skills_dir)
    
    cwd = os.getcwd()
    local_skills_dir = os.path.join(cwd, ".claude", "skills")
    if os.path.isdir(local_skills_dir):
        dirs.append(local_skills_dir)
    
    return dirs


def load_all_skills() -> Dict[str, Skill]:
    """Load all available skills from default directories"""
    skills = {}
    
    for directory in get_default_skills_directories():
        for skill in load_skills_from_directory(directory):
            skills[skill.name] = skill
    
    return skills


def get_skill(name: str) -> Optional[Skill]:
    """Get a skill by name"""
    skills = load_all_skills()
    return skills.get(name)


def list_skills() -> List[Dict[str, Any]]:
    """List all available skills"""
    skills = load_all_skills()
    return [
        {
            "name": s.name,
            "description": s.description,
            "source": s.source,
            "tags": s.tags,
        }
        for s in skills.values()
    ]


def execute_skill(name: str, arguments: Dict[str, str] = None) -> Dict[str, Any]:
    """Execute a skill with optional arguments"""
    skill = get_skill(name)
    
    if not skill:
        return {"error": f"Skill not found: {name}"}
    
    content = skill.content
    
    if arguments:
        for key, value in arguments.items():
            content = content.replace(f"{{{key}}}", value)
            content = content.replace(f"${{{key}}}", value)
    
    return {
        "name": skill.name,
        "description": skill.description,
        "content": content,
        "shell": skill.shell,
    }


def skill_list(_context: Any = None) -> Dict:
    """List all available skills"""
    skills = list_skills()
    return {
        "skills": skills,
        "count": len(skills),
    }


def skill_execute(name: str, _context: Any = None, **kwargs) -> Dict:
    """Execute a skill"""
    return execute_skill(name, kwargs)