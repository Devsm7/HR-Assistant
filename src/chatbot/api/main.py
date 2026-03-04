"""
main.py - FastAPI application for the HR Assistant.
"""

import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.chatbot.api.routes import chat, health
from src.chatbot.core.config import config
from src.chatbot.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="HR Assistant",
    description="Text-to-SQL HR chatbot with Groq and local model support",
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat.router,   prefix="/api", tags=["chat"])
app.include_router(health.router, prefix="/api", tags=["health"])


# ── Catch-all exception handler (ensures JSON, never plain-text 500) ───────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or repr(exc)},
    )


# ── Frontend ───────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the chat UI."""
    html_path = config.STATIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return """
    <html>
        <head><title>HR Assistant</title></head>
        <body>
            <h1>HR Assistant</h1>
            <p>Static files not found. Run the server from the project root.</p>
        </body>
    </html>
    """


# ── Static files ───────────────────────────────────────────────────────────────
config.STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
