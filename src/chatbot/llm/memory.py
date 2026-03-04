"""
memory.py — Conversation state and in-memory session store for the HR Assistant.

Brief:
    Manages per-session conversation history so the LLM can maintain context
    across multiple turns (e.g., follow-up questions about the same employee
    or department).

Purpose:
    At query time, the conversation history is passed alongside the retrieved
    context into the LLM prompt, enabling coherent multi-turn dialogue.
    Each session is identified by a unique session_id (e.g., user ID or
    browser session key).

Session lifecycle:
    Sessions are automatically evicted after SESSION_TTL_SECONDS of inactivity,
    or when the store exceeds SESSION_MAX_COUNT sessions (oldest evicted first).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single turn in the conversation (user or assistant)."""
    role:      str                                          # "user" or "assistant"
    content:   str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """Holds the full conversation history for one session."""
    messages:   List[Message] = Field(default_factory=list)
    last_query: Optional[str] = None
    updated_at: datetime      = Field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.utcnow()
        if role == "user":
            self.last_query = content

    def get_history(self, max_turns: int = 10) -> List[Message]:
        """Return the last N turns (user + assistant pairs) of history."""
        return self.messages[-(max_turns * 2):]

    def clear(self) -> None:
        self.messages.clear()
        self.last_query = None
        self.updated_at = datetime.utcnow()


class InMemoryStateStore:
    """
    In-memory store mapping session_id → ConversationState.

    Automatically evicts:
      - Sessions idle longer than ttl_seconds
      - Oldest sessions when count exceeds max_sessions
    """

    def __init__(self, max_sessions: int = 100, ttl_seconds: int = 3600) -> None:
        self._store:        dict[str, ConversationState] = {}
        self._max_sessions  = max_sessions
        self._ttl_seconds   = ttl_seconds

    def _evict(self) -> None:
        """Remove expired and excess sessions."""
        now = datetime.utcnow()

        # Remove TTL-expired sessions
        expired = [
            sid for sid, state in self._store.items()
            if (now - state.updated_at).total_seconds() > self._ttl_seconds
        ]
        for sid in expired:
            del self._store[sid]

        # Evict oldest sessions if over the cap
        while len(self._store) > self._max_sessions:
            oldest = min(self._store, key=lambda s: self._store[s].updated_at)
            del self._store[oldest]

    def get(self, session_id: str) -> ConversationState:
        self._evict()
        if session_id not in self._store:
            self._store[session_id] = ConversationState()
        return self._store[session_id]

    def set(self, session_id: str, state: ConversationState) -> None:
        state.updated_at = datetime.utcnow()
        self._evict()
        self._store[session_id] = state

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)


def _make_store() -> InMemoryStateStore:
    """Create store using config values (avoids circular import at module level)."""
    try:
        from ..core.config import config
        return InMemoryStateStore(
            max_sessions=config.SESSION_MAX_COUNT,
            ttl_seconds=config.SESSION_TTL_SECONDS,
        )
    except Exception:
        return InMemoryStateStore()


# Module-level singleton — import and use directly
store = _make_store()
