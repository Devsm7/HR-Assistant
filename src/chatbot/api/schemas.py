"""
Pydantic request/response models for the HR Assistant API.
"""

from typing import Literal, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    message:    str
    session_id: Optional[str]                    = "default_session"
    model:      Literal["groq", "local"]         = "groq"


class ChatResponse(BaseModel):
    response:   str
    session_id: str
    model:      str
    sql:        Optional[str] = None             # the SQL query that was executed


class ClearHistoryRequest(BaseModel):
    session_id: Optional[str] = "default_session"


class VoiceChatResponse(BaseModel):
    transcription: str
    response:      str
    session_id:    str
