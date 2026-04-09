"""Session tools for managing conversation history"""

from typing import Any, Dict, List, Optional

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter
from galaxy_destroyer.services.sessions import get_session_manager


@register_tool(
    name="session_list",
    description="List all sessions",
    category=ToolCategory.SESSION,
    parameters=[
        ToolParameter(
            name="limit",
            description="Max sessions to return",
            type="number",
            default=20,
        ),
    ],
)
def session_list(limit: int = 20, _context: Any = None) -> Dict:
    manager = get_session_manager()
    sessions = manager.list_sessions(limit)
    return {"sessions": sessions, "count": len(sessions)}


@register_tool(
    name="session_search",
    description="Search through past sessions",
    category=ToolCategory.SESSION,
    parameters=[
        ToolParameter(name="query", description="Search query", required=True),
        ToolParameter(
            name="limit", description="Max results", type="number", default=10
        ),
    ],
)
def session_search(query: str, limit: int = 10, _context: Any = None) -> Dict:
    manager = get_session_manager()
    results = manager.search_sessions(query, limit)
    return {"query": query, "results": results, "count": len(results)}


@register_tool(
    name="session_switch",
    description="Switch to a different session",
    category=ToolCategory.SESSION,
    parameters=[
        ToolParameter(name="session_id", description="Session ID", required=True),
    ],
)
def session_switch(session_id: str, _context: Any = None) -> Dict:
    manager = get_session_manager()

    if manager.set_current_session(session_id):
        session = manager.get_session(session_id)
        return {
            "switched": True,
            "session_id": session_id,
            "cwd": session.cwd if session else None,
        }

    return {"error": f"Session not found: {session_id}"}


@register_tool(
    name="session_current",
    description="Get current session info",
    category=ToolCategory.SESSION,
)
def session_current(_context: Any = None) -> Dict:
    manager = get_session_manager()
    session = manager.get_current_session()

    if not session:
        return {"error": "No session"}

    return {
        "id": session.id,
        "cwd": session.cwd,
        "title": session.title,
        "message_count": len(session.messages),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@register_tool(
    name="session_new",
    description="Create a new session",
    category=ToolCategory.SESSION,
    parameters=[
        ToolParameter(name="cwd", description="Working directory"),
        ToolParameter(name="title", description="Session title"),
    ],
)
def session_new(
    cwd: Optional[str] = None, title: Optional[str] = None, _context: Any = None
) -> Dict:
    manager = get_session_manager()
    session = manager.create_session(cwd=cwd, title=title)
    return {
        "id": session.id,
        "cwd": session.cwd,
        "title": session.title,
        "created_at": session.created_at,
    }


@register_tool(
    name="session_delete",
    description="Delete a session",
    category=ToolCategory.SESSION,
    parameters=[
        ToolParameter(name="session_id", description="Session ID", required=True),
    ],
)
def session_delete(session_id: str, _context: Any = None) -> Dict:
    manager = get_session_manager()

    if manager.delete_session(session_id):
        return {"deleted": True, "session_id": session_id}

    return {"error": f"Session not found: {session_id}"}
