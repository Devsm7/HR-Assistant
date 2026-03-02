"""
FastAPI Web Interface for Twuaiq RAG Assistant
Bilingual support (English/Arabic) with voice input using faster-whisper
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from twuaqirag.api.routes import chat, stt, health

# Initialize FastAPI app
app = FastAPI(
    title="Twuaiq RAG Assistant",
    description="Bilingual AI Assistant for Twuaiq Academy",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(stt.router, prefix="/api", tags=["speech-to-text"])
app.include_router(health.router, prefix="/api", tags=["health"])

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    html_path = Path(__file__).parent.parent.parent.parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding='utf-8')
    return """
    <html>
        <head><title>Twuaiq RAG Assistant</title></head>
        <body>
            <h1>Welcome to Twuaiq RAG Assistant</h1>
            <p>The interface is loading...</p>
            <p>If you see this message, please ensure the static files are properly set up.</p>
        </body>
    </html>
    """

# Mount static files
static_dir = Path(__file__).parent.parent.parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
