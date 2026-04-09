"""Task tools for Galaxy Destroyer"""

from typing import Any, Dict, Optional

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter
from galaxy_destroyer.services.tasks import (
    TaskStatus,
    get_task_store,
)


@register_tool(
    name="task_create",
    description="Create a new task",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="title", description="Task title", required=True),
        ToolParameter(name="description", description="Task description", default=""),
        ToolParameter(
            name="priority",
            description="Priority (low/medium/high/urgent)",
            default="medium",
        ),
        ToolParameter(name="status", description="Initial status", default="pending"),
    ],
)
def task_create(
    title: str,
    description: str = "",
    priority: str = "medium",
    status: str = "pending",
    _context: Any = None,
) -> Dict:
    store = get_task_store()
    task = store.create(title, description, priority)
    if status != "pending":
        store.update(task.id, status=status)
        task = store.get(task.id)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "priority": task.priority.value,
        "created_at": task.created_at,
    }


@register_tool(
    name="task_get",
    description="Get task details by ID",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="task_id", description="Task ID", required=True),
    ],
)
def task_get(task_id: str, _context: Any = None) -> Dict:
    store = get_task_store()
    task = store.get(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}
    return task.to_dict()


@register_tool(
    name="task_list",
    description="List tasks with optional filters",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="status", description="Filter by status"),
        ToolParameter(name="priority", description="Filter by priority"),
        ToolParameter(
            name="limit", description="Max results", type="number", default=50
        ),
    ],
)
def task_list(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    _context: Any = None,
) -> Dict:
    store = get_task_store()
    tasks = store.list(status=status, priority=priority)[:limit]
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


@register_tool(
    name="task_update",
    description="Update a task",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="task_id", description="Task ID", required=True),
        ToolParameter(name="status", description="New status"),
        ToolParameter(name="title", description="New title"),
        ToolParameter(name="description", description="New description"),
        ToolParameter(name="priority", description="New priority"),
    ],
)
def task_update(
    task_id: str,
    status: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    _context: Any = None,
) -> Dict:
    store = get_task_store()
    updates = {}
    if status:
        updates["status"] = status
    if title:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if priority:
        updates["priority"] = priority
    task = store.update(task_id, **updates)
    if not task:
        return {"error": f"Task not found: {task_id}"}
    return task.to_dict()


@register_tool(
    name="task_stop",
    description="Stop/cancel a task",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="task_id", description="Task ID", required=True),
    ],
)
def task_stop(task_id: str, _context: Any = None) -> Dict:
    store = get_task_store()
    task = store.update(task_id, status="cancelled")
    if not task:
        return {"error": f"Task not found: {task_id}"}
    return {"id": task.id, "status": "cancelled"}


@register_tool(
    name="todo_write",
    description="Write a todo item (simple task)",
    category=ToolCategory.TASKS,
    parameters=[
        ToolParameter(name="content", description="Todo content", required=True),
        ToolParameter(name="status", description="Status", default="pending"),
    ],
)
def todo_write(content: str, status: str = "pending", _context: Any = None) -> Dict:
    store = get_task_store()
    task = store.create(title=content, description=status)
    if status != "pending":
        store.update(task.id, status=status)
        task = store.get(task.id)
    return {"id": task.id, "content": task.title, "status": task.status.value}
