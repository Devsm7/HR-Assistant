"""
run.py - Start the HR Assistant FastAPI server with uvicorn.

Usage:
    python src/run.py
"""

import sys
from pathlib import Path

# Ensure the project root (parent of src/) is on sys.path so that
# 'src.chatbot.*' imports resolve correctly when this file is run directly.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import uvicorn

from src.chatbot.core.config import config

if __name__ == "__main__":
    print("=" * 55)
    print("  HR Assistant  -  starting FastAPI server")
    print(f"  UI  : http://localhost:{config.API_PORT}")
    print(f"  Docs: http://localhost:{config.API_PORT}/docs")
    print("  Press Ctrl+C to stop")
    print("=" * 55)

    uvicorn.run(
        "src.chatbot.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
        log_level="info",
    )
