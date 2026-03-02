"""
Local development server runner
Run the FastAPI application using uvicorn
"""
import uvicorn
from twuaqirag.core.config import config


if __name__ == "__main__":
    print("🚀 Starting Twuaiq RAG Assistant FastAPI Server...")
    print(f"🌐 The interface will be available at: http://localhost:{config.API_PORT}")
    print(f"📱 API documentation at: http://localhost:{config.API_PORT}/docs")
    print("\n⏹️  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(
        "twuaqirag.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
