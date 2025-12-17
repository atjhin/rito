import os
from pathlib import Path


class Config:
    """Application configuration and path management."""
    
    # Base directory (project root)
    BASE_DIR = Path(__file__).parent.parent.parent
    
    # Source directory
    SRC_DIR = BASE_DIR / "src"
    
    # Logs directory
    LOGS_DIR = SRC_DIR / "logs"
    
    # Data directory
    DATA_DIR = BASE_DIR / "data"
    
    # Database paths
    LANGGRAPH_CHECKPOINTS_DB = LOGS_DIR / "langgraph_checkpoints.sqlite"
    
    # Graph visualization path
    GRAPH_VISUALIZATION_PATH = LOGS_DIR / "graph.png"
    
    # Champions file path
    CHAMPIONS_FILE = DATA_DIR / "champions.txt"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)


# Initialize directories when module is imported
Config.ensure_directories()

