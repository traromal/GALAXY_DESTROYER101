"""Session management system"""

import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    id: str
    cwd: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "cwd": self.cwd,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "metadata": self.metadata,
            "title": self.title,
        }


class SessionManager:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.path.join(
                os.path.expanduser("~"), ".galaxy_destroyer", "sessions"
            )

        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        self._sessions: Dict[str, Session] = {}
        self._current_session: Optional[Session] = None
        self._load_sessions()

    def _session_path(self, session_id: str) -> str:
        safe_id = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_dir, f"{safe_id}.json")

    def _load_sessions(self):
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    session = Session(
                        id=data["id"],
                        cwd=data.get("cwd", ""),
                        created_at=data.get("created_at", time.time()),
                        updated_at=data.get("updated_at", time.time()),
                        messages=data.get("messages", []),
                        metadata=data.get("metadata", {}),
                        title=data.get("title"),
                    )
                    self._sessions[session.id] = session
                except Exception:
                    pass

    def _save_session(self, session: Session):
        session.updated_at = time.time()
        filepath = self._session_path(session.id)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

    def create_session(
        self, cwd: Optional[str] = None, title: Optional[str] = None
    ) -> Session:
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            cwd=cwd or os.getcwd(),
            title=title,
        )
        self._sessions[session_id] = session
        self._current_session = session
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_current_session(self) -> Optional[Session]:
        if self._current_session is None:
            self._current_session = self.create_session()
        return self._current_session

    def set_current_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            self._current_session = session
            return True
        return False

    def add_message(
        self, role: str, content: str, metadata: Optional[Dict] = None
    ) -> Session:
        session = self.get_current_session()
        if session:
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time(),
                "metadata": metadata or {},
            }
            session.messages.append(message)
            self._save_session(session)
        return session

    def list_sessions(self, limit: int = 20) -> List[Dict]:
        sessions = sorted(
            self._sessions.values(), key=lambda s: s.updated_at, reverse=True
        )
        return [
            {
                "id": s.id,
                "cwd": s.cwd,
                "title": s.title or f"Session {s.id[:8]}",
                "message_count": len(s.messages),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for s in sessions[:limit]
        ]

    def search_sessions(self, query: str, limit: int = 10) -> List[Dict]:
        query_lower = query.lower()
        results = []

        for session in self._sessions.values():
            if query_lower in session.title.lower() if session.title else False:
                results.append(session)
                continue

            for msg in session.messages:
                if query_lower in msg.get("content", "").lower():
                    results.append(session)
                    break

        results = sorted(results, key=lambda s: s.updated_at, reverse=True)
        return [
            {
                "id": s.id,
                "title": s.title or f"Session {s.id[:8]}",
                "cwd": s.cwd,
                "preview": s.messages[-1].get("content", "")[:100]
                if s.messages
                else "",
            }
            for s in results[:limit]
        ]

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            filepath = self._session_path(session_id)
            if os.path.exists(filepath):
                os.remove(filepath)
            if self._current_session and self._current_session.id == session_id:
                self._current_session = None
            return True
        return False

    def update_title(self, session_id: str, title: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.title = title
            self._save_session(session)
            return True
        return False

    def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        session = self._sessions.get(session_id)
        if not session:
            return []

        messages = session.messages
        if limit:
            messages = messages[-limit:]

        return messages


_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
