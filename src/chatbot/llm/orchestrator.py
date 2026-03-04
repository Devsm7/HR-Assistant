"""
orchestrator.py - Main entry point for the HR Assistant Text-to-SQL pipeline.

Pipeline per user turn:
  1. Resolve the LLM provider (Groq or local) from model_choice
  2. Load conversation history from memory
  3. Generate SQL from the user question (via LLM) — history passed for multi-turn context
  4. Execute SQL on local SQLite database
  5. Ask LLM to format the result into a natural language answer
  6. Save both turns to memory

The function is async to avoid blocking the FastAPI event loop — synchronous
LLM and DB calls are offloaded to a thread pool via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import logging

from .memory import store
from .prompts import ANSWER_PROMPT
from .providers import BaseProvider, ModelChoice, get_provider
from ...sql.sql_engine import run as sql_run
from ...chatbot.core.config import config

logger = logging.getLogger(__name__)


# ── Answer formatting (sync — called via to_thread) ───────────────────────────

def _format_answer(question: str, sql_result: str, provider: BaseProvider) -> str:
    """Call the LLM to format the SQL result into a natural language answer."""
    system_msg = ANSWER_PROMPT.format(
        sql_result=sql_result,
        question=question,
    )
    return provider.chat_completion(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": question},
        ],
        max_tokens=512,
        temperature=0.0,
    )


# ── Main async entry point ────────────────────────────────────────────────────

async def generate_response(
    user_message: str,
    session_id:   str         = "default",
    model_choice: ModelChoice = ModelChoice.GROQ,
) -> tuple[str, str]:
    """
    Run the full Text-to-SQL pipeline for one user turn.

    Args:
        user_message: The question from the user.
        session_id:   Unique key for conversation memory.
        model_choice: Which LLM backend to use ("groq" or "local").

    Returns:
        (answer, sql) — the natural language answer and the SQL query that was run.
    """
    provider = get_provider(model_choice)
    logger.info("[%s] model=%s  question=%r", session_id, provider.model_id, user_message)

    # 1) Load conversation history
    state   = store.get(session_id)
    history = state.get_history(max_turns=config.SESSION_MAX_TURNS)

    # Convert Message objects → plain dicts for sql_engine
    history_dicts = [{"role": m.role, "content": m.content} for m in history]

    # 2 & 3) Generate SQL + execute (in thread pool — both are sync/blocking)
    sql, sql_result = await asyncio.to_thread(
        sql_run, user_message, provider, history_dicts
    )
    logger.info("[%s] SQL: %s", session_id, sql)
    logger.debug("[%s] SQL result: %s", session_id, sql_result[:200])

    # 4) Format result into natural language (in thread pool)
    answer = await asyncio.to_thread(
        _format_answer, user_message, sql_result, provider
    )

    # 5) Save turn to memory
    state.add_message(role="user",      content=user_message)
    state.add_message(role="assistant", content=answer)
    store.set(session_id, state)

    return answer, sql
