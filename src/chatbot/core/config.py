"""
Environment variables and configuration
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    DATASETS_DIR = PROJECT_ROOT / "datasets"
    CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
    STATIC_DIR = PROJECT_ROOT / "static"
    MODELS_DIR = PROJECT_ROOT / "models"
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Model settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.2")  # Deprecated: use LLM_MODEL_ENGLISH/ARABIC
    LLM_MODEL_ENGLISH: str = os.getenv("LLM_MODEL_ENGLISH", "llama3.2")
    LLM_MODEL_ARABIC: str = os.getenv("LLM_MODEL_ARABIC", "aya")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "medium")
    
    # Whisper settings
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    
    # Retrieval settings
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "20"))  # Increased to retrieve more documents
    
    # Database files
    BOOTCAMPS_CSV: Path = DATASETS_DIR / "bootcamps_new.csv"
    PLACES_CSV: Path = DATASETS_DIR / "places_new.csv"


config = Config()
