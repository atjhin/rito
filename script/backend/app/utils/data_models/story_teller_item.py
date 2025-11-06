from dataclasses import dataclass
from typing import Any, Dict, List
from script.backend.app.utils.core.logger import Logger

@dataclass
class StoryTellerItem:
    """
    Item that is given to the StoryTeller.
    """
    scenario: str
    champions: List[Dict[str, Any]]
    logger: Logger
    
