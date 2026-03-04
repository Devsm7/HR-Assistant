"""
Chat endpoint - handles text-based chat messages.
"""

import logging
import traceback

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from src.chatbot.api.schemas import ChatMessage, ChatResponse, ClearHistoryRequest
from src.chatbot.llm.orchestrator import generate_response
from src.chatbot.llm.providers import ModelChoice
from src.chatbot.llm.memory import store

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Handle a text chat message and return an AI-generated answer."""
    if not chat_message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        model_choice = ModelChoice(chat_message.model)
        answer, sql  = await generate_response(
            user_message=chat_message.message,
            session_id=chat_message.session_id,
            model_choice=model_choice,
        )
    except ValueError as e:
        logger.error("ValueError in /api/chat: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unhandled exception in /api/chat: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e) or repr(e))

    return ChatResponse(
        response=answer,
        session_id=chat_message.session_id,
        model=chat_message.model,
        sql=sql,
    )


@router.post("/clear-history")
async def clear_history(request: ClearHistoryRequest):
    """Clear conversation history for a session."""
    store.delete(request.session_id)
    return {"message": "History cleared", "session_id": request.session_id}
