"""
providers.py - Dual-model provider layer for the HR Assistant.

Supports two backends, selectable per request:
  - "groq"  : Groq API (llama-3.3-70b-versatile) — fast cloud inference
  - "local" : Local HuggingFace model (Qwen/Qwen2.5-7B-Instruct) — runs on device

Both implement the same BaseProvider interface so the rest of the pipeline
is completely model-agnostic.

Usage:
    from src.chatbot.llm.providers import get_provider, ModelChoice
    provider = get_provider(ModelChoice.GROQ)
    answer = provider.chat_completion(messages, max_tokens=256, temperature=0.0)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import tenacity

logger = logging.getLogger(__name__)


# ── Model choice ──────────────────────────────────────────────────────────────

class ModelChoice(str, Enum):
    GROQ  = "groq"
    LOCAL = "local"


# ── Abstract base ─────────────────────────────────────────────────────────────

class BaseProvider(ABC):
    """Common interface for all LLM backends."""

    @abstractmethod
    def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...


# ── Groq provider ─────────────────────────────────────────────────────────────

class GroqProvider(BaseProvider):
    """Calls the Groq cloud API with automatic retry on transient errors."""

    def __init__(self, model_id: str, api_key: str) -> None:
        from groq import Groq
        self._client = Groq(api_key=api_key)
        self._model  = model_id
        logger.info("GroqProvider ready — model: %s", model_id)

    @property
    def model_id(self) -> str:
        return self._model

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()


# ── Local HuggingFace provider ────────────────────────────────────────────────

class LocalHFProvider(BaseProvider):
    """
    Runs a HuggingFace model locally using transformers.pipeline.

    The model is downloaded once and cached by HuggingFace Hub.
    On first use it may take a few minutes to download Qwen2.5-7B (~14 GB).
    Subsequent starts are fast (loaded from cache).
    """

    def __init__(self, model_id: str) -> None:
        import torch
        from transformers import pipeline

        logger.info("Loading local model: %s  (this may take a moment on first run)...", model_id)

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self._pipe  = pipeline(
            "text-generation",
            model=model_id,
            device_map="auto",
            torch_dtype=dtype,
        )
        self._model = model_id
        logger.info("Local model loaded: %s", model_id)

    @property
    def model_id(self) -> str:
        return self._model

    def chat_completion(
        self,
        messages: list[dict],
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        gen_kwargs: dict = {"max_new_tokens": max_tokens, "return_full_text": False}
        if temperature > 0:
            gen_kwargs["do_sample"]   = True
            gen_kwargs["temperature"] = temperature
        else:
            gen_kwargs["do_sample"] = False

        result = self._pipe(messages, **gen_kwargs)
        logger.debug("Local model raw output: %s", result)

        # transformers pipeline returns different shapes depending on version / mode:
        # - Chat template + return_full_text=False:
        #     [[{"role": "assistant", "content": "..."}]]
        # - Plain text: [{"generated_text": "..."}]
        # - Or:         [{"generated_text": [{...messages...}]}]
        try:
            output = result[0]
            if isinstance(output, list):
                output = output[0]

            text = output.get("generated_text", "")

            # Chat format: generated_text is a list of message dicts
            if isinstance(text, list):
                for msg in reversed(text):
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        return str(msg.get("content", "")).strip()
                # Fallback: last item's content
                return str(text[-1].get("content", "")).strip()

            return str(text).strip()

        except Exception as e:
            logger.error("Failed to parse local model output: %s | raw: %s", e, result)
            raise


# ── Singleton registry ────────────────────────────────────────────────────────

_groq_provider:  Optional[GroqProvider]    = None
_local_provider: Optional[LocalHFProvider] = None


def get_provider(choice: ModelChoice) -> BaseProvider:
    """
    Return the singleton provider for the requested model choice.
    Providers are lazy-loaded on first call.
    """
    global _groq_provider, _local_provider

    from ..core.config import config

    if choice == ModelChoice.GROQ:
        if _groq_provider is None:
            if not config.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is not set. Add it to your .env file: GROQ_API_KEY=gsk_..."
                )
            _groq_provider = GroqProvider(
                model_id=config.GROQ_MODEL_ID,
                api_key=config.GROQ_API_KEY,
            )
        return _groq_provider

    # ModelChoice.LOCAL
    if _local_provider is None:
        _local_provider = LocalHFProvider(model_id=config.LOCAL_MODEL_ID)
    return _local_provider
