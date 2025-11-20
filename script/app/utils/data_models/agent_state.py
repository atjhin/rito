from typing import List, TypedDict
from langchain_core.messages import BaseMessage
from app.utils.constants.models import ModelChoices

class AgentState(TypedDict, total=False):
    """Runtime state passed between graph nodes."""

    messages: List[BaseMessage]
    model: ModelChoices
    next_bot: List[str]
    event_list: List[str]
    ai_response: str
