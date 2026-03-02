"""
Chat endpoint - handles text-based chat messages
"""
from fastapi import APIRouter, HTTPException
from twuaqirag.api.schemas import ChatMessage, ChatResponse, ClearHistoryRequest
from twuaqirag.rag.orchestrator import generate_response
from twuaqirag.rag.memory import store
from langchain_community.chat_message_histories import ChatMessageHistory

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Handle text chat messages"""
    if not chat_message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    response = await generate_response(chat_message.message, chat_message.session_id)
    
    return ChatResponse(
        response=response,
        session_id=chat_message.session_id
    )


@router.post("/clear-history")
async def clear_history(request: ClearHistoryRequest):
    """Clear conversation history for a session"""
    session_id = request.session_id
    if session_id in store:
        store[session_id] = ChatMessageHistory()
    
    return {"message": "History cleared", "session_id": session_id}
