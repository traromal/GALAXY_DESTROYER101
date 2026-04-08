"""Task management system - full implementation"""

import json
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    assignee: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "tags": self.tags,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "assignee": self.assignee,
        }


class TaskStore:
    """Task storage and management"""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".galaxy_destroyer", "tasks.json")
        
        self.storage_path = storage_path
        self._tasks: Dict[str, Task] = {}
        self._load()
    
    def _load(self):
        """Load tasks from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = Task(
                            id=task_data["id"],
                            title=task_data["title"],
                            description=task_data.get("description", ""),
                            status=TaskStatus(task_data.get("status", "pending")),
                            priority=TaskPriority(task_data.get("priority", "medium")),
                            created_at=task_data.get("created_at", time.time()),
                            updated_at=task_data.get("updated_at", time.time()),
                            completed_at=task_data.get("completed_at"),
                            tags=task_data.get("tags", []),
                            metadata=task_data.get("metadata", {}),
                            parent_id=task_data.get("parent_id"),
                            assignee=task_data.get("assignee"),
                        )
                        self._tasks[task.id] = task
            except Exception:
                pass
    
    def _save(self):
        """Save tasks to storage"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            "tasks": [task.to_dict() for task in self._tasks.values()],
            "updated_at": time.time(),
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create(self, title: str, description: str = "", priority: str = "medium", 
               tags: List[str] = None, metadata: Dict[str, Any] = None) -> Task:
        """Create a new task"""
        task_id = f"task_{int(time.time() * 1000)}"
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=TaskPriority(priority),
            tags=tags or [],
            metadata=metadata or {},
        )
        self._tasks[task_id] = task
        self._save()
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self._tasks.get(task_id)
    
    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        for key, value in kwargs.items():
            if key == "status":
                value = TaskStatus(value)
            elif key == "priority":
                value = TaskPriority(value)
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = time.time()
        if kwargs.get("status") == "completed" and not task.completed_at:
            task.completed_at = time.time()
        
        self._save()
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save()
            return True
        return False
    
    def list(self, status: Optional[str] = None, priority: Optional[str] = None,
             tags: List[str] = None) -> List[Task]:
        """List tasks with optional filters"""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        
        if priority:
            tasks = [t for t in tasks if t.priority.value == priority]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    def clear(self):
        """Clear all tasks"""
        self._tasks.clear()
        self._save()


_store: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    """Get the global task store"""
    global _store
    if _store is None:
        _store = TaskStore()
    return _store


def task_create(title: str, description: str = "", priority: str = "medium",
                tags: List[str] = None, _context: Any = None) -> Dict:
    """Create a new task"""
    store = get_task_store()
    task = store.create(title, description, priority, tags)
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status.value,
        "priority": task.priority.value,
        "created_at": task.created_at,
    }


def task_get(task_id: str, _context: Any = None) -> Dict:
    """Get a task by ID"""
    store = get_task_store()
    task = store.get(task_id)
    if not task:
        return {"error": f"Task not found: {task_id}"}
    return task.to_dict()


def task_list(status: Optional[str] = None, priority: Optional[str] = None,
              _context: Any = None) -> Dict:
    """List all tasks"""
    store = get_task_store()
    tasks = store.list(status, priority)
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks),
    }


def task_update(task_id: str, status: Optional[str] = None, title: Optional[str] = None,
                description: Optional[str] = None, priority: Optional[str] = None,
                _context: Any = None) -> Dict:
    """Update a task"""
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


def task_delete(task_id: str, _context: Any = None) -> Dict:
    """Delete a task"""
    store = get_task_store()
    if store.delete(task_id):
        return {"deleted": True, "task_id": task_id}
    return {"error": f"Task not found: {task_id}"}


def task_stop(task_id: str, _context: Any = None) -> Dict:
    """Stop/cancel a task"""
    store = get_task_store()
    task = store.update(task_id, status="cancelled")
    if not task:
        return {"error": f"Task not found: {task_id}"}
    return {"status": "cancelled", "task_id": task_id}


def todo_write(content: str, status: str = "pending", _context: Any = None) -> Dict:
    """Write a todo item (simple task)"""
    store = get_task_store()
    task = store.create(title=content, description=status)
    return {"id": task.id, "content": content, "status": status}