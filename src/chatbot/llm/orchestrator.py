"""
orchestrator.py - Main entry point for the HR Assistant Text-to-SQL pipeline.

Pipeline per user turn:
  1. Load conversation history from memory
  2. Generate SQL from the user question (via LLM)
  3. Execute SQL on local SQLite database
  4. Ask LLM to format the result into a natural language answer
  5. Save both turns to memory
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from .prompts import ANSWER_PROMPT
from .memory import store
from ...sql.sql_engine import run as sql_run

# ── Config ────────────────────────────────────────────────────────────────────
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_FILE)

MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
_client  = InferenceClient(model=MODEL_ID, token=os.getenv("HF_TOKEN"))


def _format_answer(question: str, sql_result: str) -> str:
    """Call the LLM to format the SQL result into a natural language answer."""
    system_msg = ANSWER_PROMPT.format(
        sql_result=sql_result,
        question=question,
    )
    response = _client.chat_completion(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": question},
        ],
        max_tokens=512,
        temperature=0.0,   # fully deterministic — no creativity when reading numbers
    )
    return response.choices[0].message.content.strip()


def generate_response(user_message: str, session_id: str = "default") -> str:
    """
    Run the full Text-to-SQL pipeline for one user turn.

    Args:
        user_message: The question from the user.
        session_id:   Unique key for conversation memory.

    Returns:
        The assistant's natural language answer.
    """
    # 1) Load conversation history
    state = store.get(session_id)

    # 2 & 3) Generate SQL + execute on SQLite
    sql, sql_result = sql_run(user_message)

    # 4) Format result into natural language
    answer = _format_answer(
        question=user_message,
        sql_result=sql_result,
    )

    # 5) Save turn to memory
    state.add_message(role="user",      content=user_message)
    state.add_message(role="assistant", content=answer)
    store.set(session_id, state)

    return answer
