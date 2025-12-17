"""Configuration for the Flask API service."""

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Flask API service configuration."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Static and template directories
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"
    
    # LangGraph service URL
    # In Cloud Run, this will be the internal service URL
    LANGGRAPH_SERVICE_URL = os.getenv(
        "LANGGRAPH_SERVICE_URL",
        "http://localhost:8080"  # Default for local development
    )
    
    # Request timeout for LangGraph service (story generation can take time)
    LANGGRAPH_TIMEOUT = int(os.getenv("LANGGRAPH_TIMEOUT", "300"))  # 5 minutes default
    
    # Google API key for input validation
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


Config.ensure_directories()

