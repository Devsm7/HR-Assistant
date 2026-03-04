"""
Health check endpoint.
"""

from fastapi import APIRouter

from src.chatbot.core.config import config

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return service health and active model configuration."""
    return {
        "status":      "healthy",
        "groq_model":  config.GROQ_MODEL_ID,
        "local_model": config.LOCAL_MODEL_ID,
    }
