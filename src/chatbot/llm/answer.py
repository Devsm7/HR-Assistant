"""
answer.py - LLM answer generation for the HR Assistant RAG pipeline.

Brief:
    Calls the Falcon-Arabic-7B model via the HuggingFace Inference API
    (no local download required).

Purpose:
    At query time, this module assembles the full message list
    (system prompt + conversation history + current question) and calls
    the HuggingFace API to produce a response. It does NOT perform
    retrieval - that is handled upstream by vector_store.py and formatting.py.

Pipeline position:
    formatting.docs_to_context()
        => generate_answer()  <- (this file)
            => LLM response returned to caller

Setup:
    Set your HuggingFace token in the environment:
        export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
    Or create a .env file with:
        HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from .prompts import SYSTEM_PROMPT
from .memory import Message

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_FILE)

# ── Model config ──────────────────────────────────────────────────────────────
MODEL_ID  = "meta-llama/Meta-Llama-3-8B-Instruct"
HF_TOKEN  = os.getenv("HF_TOKEN")          # set in .env or environment

# ── HuggingFace Inference client (initialized once) ───────────────────────────
_client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)


# ── Input dataclass ───────────────────────────────────────────────────────────
@dataclass
class AnswerInput:
    """Everything needed to generate one answer."""
    question: str                                          # current user query
    context: str                                           # formatted retrieved docs
    history: List[Message] = field(default_factory=list)  # past turns from memory
    style_hint: Optional[str] = None                       # optional extra instruction


# ── Prompt assembly ───────────────────────────────────────────────────────────
def _build_messages(inp: AnswerInput) -> list[dict]:
    """
    Build the messages list for the chat completion API call:
        [system] + [history turns] + [current user question]
    """
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=inp.context)},
    ]

    for msg in inp.history:
        messages.append({"role": msg.role, "content": msg.content})

    question = inp.question
    if inp.style_hint:
        question = f"{question}\n\n({inp.style_hint})"

    messages.append({"role": "user", "content": question})
    return messages


# ── Answer generation ─────────────────────────────────────────────────────────
def generate_answer(inp: AnswerInput) -> str:
    """
    Generate an answer by calling the HuggingFace Inference API.

    Args:
        inp: AnswerInput with the question, retrieved context, and history.

    Returns:
        The model's answer as a plain string.
    """
    messages = _build_messages(inp)

    response = _client.chat_completion(
        messages=messages,
        max_tokens=512,
        temperature=0.1,    # low temperature for factual HR answers
    )

    return response.choices[0].message.content.strip()
