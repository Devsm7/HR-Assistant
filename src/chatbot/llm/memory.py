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
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single turn in the conversation (user or assistant)."""
    role: str                  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """Holds the full conversation history for one session."""
    messages: List[Message] = Field(default_factory=list)
    last_query: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

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
    """Simple in-memory store mapping session_id → ConversationState."""

    def __init__(self):
        self._store: dict[str, ConversationState] = {}

    def get(self, session_id: str) -> ConversationState:
        if session_id not in self._store:
            self._store[session_id] = ConversationState()
        return self._store[session_id]

    def set(self, session_id: str, state: ConversationState) -> None:
        state.updated_at = datetime.utcnow()
        self._store[session_id] = state

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)


# Module-level singleton — import and use directly
store = InMemoryStateStore()
