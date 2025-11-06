from dataclasses import dataclass, field
from typing import Any, Dict, List
from langchain_core.messages import BaseMessage
from script.backend.app.utils.core.logger import Logger


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

