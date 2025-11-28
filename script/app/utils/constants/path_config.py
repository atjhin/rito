import os

class Config:
    # Base directory (project root)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Logs directory
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    
    # Database paths
    LANGGRAPH_CHECKPOINTS_DB = os.path.join(LOGS_DIR, "langgraph_checkpoints.sqlite")

    GRAPH_VISUALIZATION_PATH = os.path.join(LOGS_DIR, "graph.png")
    
    # Ensure directories exist
    @classmethod
    def ensure_directories(cls):
        os.makedirs(cls.LOGS_DIR, exist_ok=True)

# Initialize directories when module is imported
Config.ensure_directories()