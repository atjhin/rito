from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage

@dataclass
class StoryTellerItem:
    """
    Item that is given to the StoryTeller.
    """
    scenario: str
    champions: List[Dict[str, Any]]
    

@dataclass
class AgentCallItem: 
    """
    Item that represents a single LLM invocation by an agent in the StoryTeller system.
    """
    agent_role_name: str
    model_name: str
    messages: List[BaseMessage]
    output_message: BaseMessage

    def __init__(
        self,
        agent_role_name: str,
        model_name: str,
        messages: List[BaseMessage],
        output_message: BaseMessage,
    ):
        self.agent_role_name = agent_role_name
        self.model_name = model_name
        self.messages = messages
        self.output_message = output_message

