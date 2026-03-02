"""
Pydantic request/response models for API
"""
from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"


class ChatResponse(BaseModel):
    response: str
    session_id: str


class ClearHistoryRequest(BaseModel):
    session_id: Optional[str] = "default_session"


class VoiceChatResponse(BaseModel):
    transcription: str
    response: str
    session_id: str
