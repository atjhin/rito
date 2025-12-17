from dataclasses import dataclass
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.logger import Logger


@dataclass
class StoryTellerItem:
    """Configuration item for the StoryTeller."""
    scenario: str
    champions: List[Dict[str, Any]]
    logger: "Logger"

