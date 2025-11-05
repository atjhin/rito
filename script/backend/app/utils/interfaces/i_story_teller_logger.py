from abc import ABC, abstractmethod
from typing import Dict, Any

class IStoryTellerLogger(ABC):
    @abstractmethod
    def log_story_teller_instance(self, event: str, details: Dict[str, Any]):
        """
        Log a story teller instance with associated details.

        Parameters
        ----------
        event : str
            The name of the event to log.
        details : Dict[str, Any]
            Additional details about the event.
        """
        pass

