"""Session history management - stores conversation history"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """A message in the conversation"""
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)


@dataclass
class Session:
    """A conversation session"""
    id: str
    created_at: float
    updated_at: float
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "tool_calls": m.tool_calls,
                    "tool_results": m.tool_results,
                }
                for m in self.messages
            ],
            "metadata": self.metadata,
        }


class HistoryManager:
    """Manages conversation history"""
    
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".galaxy_destroyer", "history.json")
        
        self.storage_path = storage_path
        self._sessions: Dict[str, Session] = {}
        self._current_session_id: Optional[str] = None
        self._load()
    
    def _load(self):
        """Load history from disk"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                for session_data in data.get("sessions", []):
                    session = Session(
                        id=session_data["id"],
                        created_at=session_data["created_at"],
                        updated_at=session_data["updated_at"],
                        metadata=session_data.get("metadata", {}),
                    )
                    for msg_data in session_data.get("messages", []):
                        session.messages.append(Message(
                            role=msg_data["role"],
                            content=msg_data["content"],
                            timestamp=msg_data.get("timestamp", time.time()),
                            tool_calls=msg_data.get("tool_calls", []),
                            tool_results=msg_data.get("tool_results", []),
                        ))
                    self._sessions[session.id] = session
                
                self._current_session_id = data.get("current_session")
            except Exception:
                pass
    
    def _save(self):
        """Save history to disk"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        data = {
            "current_session": self._current_session_id,
            "sessions": [
                session.to_dict() 
                for session in self._sessions.values()
            ],
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_session(self, metadata: Dict = None) -> Session:
        """Create a new session"""
        import uuid
        session_id = f"session_{int(time.time())}"
        
        session = Session(
            id=session_id,
            created_at=time.time(),
            updated_at=time.time(),
            metadata=metadata or {},
        )
        
        self._sessions[session_id] = session
        self._current_session_id = session_id
        self._save()
        
        return session
    
    def get_current_session(self) -> Optional[Session]:
        """Get current session"""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        
        return self.create_session()
    
    def add_message(self, role: str, content: str):
        """Add a message to current session"""
        session = self.get_current_session()
        if session:
            session.add_message(role, content)
            self._save()
    
    def get_messages(self, session_id: str = None) -> List[Message]:
        """Get messages from a session"""
        if session_id:
            session = self._sessions.get(session_id)
        else:
            session = self.get_current_session()
        
        return session.messages if session else []
    
    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent sessions"""
        sessions = sorted(
            self._sessions.values(), 
            key=lambda s: s.updated_at, 
            reverse=True
        )[:limit]
        
        return [
            {
                "id": s.id,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages),
                "preview": s.messages[0].content[:50] if s.messages else "",
                "metadata": s.metadata,
            }
            for s in sessions
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._current_session_id == session_id:
                self._current_session_id = None
            self._save()
            return True
        return False
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session"""
        if session_id in self._sessions:
            self._current_session_id = session_id
            self._save()
            return True
        return False
    
    def clear_all(self):
        """Clear all history"""
        self._sessions.clear()
        self._current_session_id = None
        self._save()


_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """Get global history manager"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager


def add_user_message(content: str):
    """Add a user message to history"""
    get_history_manager().add_message("user", content)


def add_assistant_message(content: str):
    """Add an assistant message to history"""
    get_history_manager().add_message("assistant", content)


def get_conversation_history() -> List[Dict]:
    """Get conversation history for API"""
    history = get_history_manager()
    messages = history.get_messages()
    
    return [
        {"role": m.role, "content": m.content}
        for m in messages
    ]


def list_recent_sessions(limit: int = 10) -> List[Dict]:
    """List recent sessions"""
    return get_history_manager().list_sessions(limit)


def clear_history():
    """Clear all history"""
    get_history_manager().clear_all()