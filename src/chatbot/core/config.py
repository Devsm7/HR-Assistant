"""
config.py - Application configuration for the HR Assistant.

All settings can be overridden via environment variables or the project .env file.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_FILE)


class Config:
    # ── Paths ─────────────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]
    DB_PATH:      Path = PROJECT_ROOT / "hr.db"
    STATIC_DIR:   Path = PROJECT_ROOT / "static"

    # ── API server ─────────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # ── Groq ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY:  str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL_ID: str = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile")

    # ── Local HuggingFace model ────────────────────────────────────────────────
    LOCAL_MODEL_ID: str = os.getenv("LOCAL_MODEL_ID", "Qwen/Qwen2.5-7B-Instruct")

    # ── Session memory ─────────────────────────────────────────────────────────
    SESSION_MAX_TURNS:   int = int(os.getenv("SESSION_MAX_TURNS",   "10"))
    SESSION_MAX_COUNT:   int = int(os.getenv("SESSION_MAX_COUNT",   "100"))
    SESSION_TTL_SECONDS: int = int(os.getenv("SESSION_TTL_SECONDS", "3600"))

    # ── SQL engine ─────────────────────────────────────────────────────────────
    SQL_MAX_ROWS: int = int(os.getenv("SQL_MAX_ROWS", "50"))


config = Config()
