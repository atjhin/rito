from dataclasses import dataclass
from typing import List
from langchain_core.messages import BaseMessage

@dataclass
class AgentLoggerItem: 
    """
    Item that represents a single LLM invocation by an agent in the StoryTeller system.
    """
    agent_role_name: str
    model_name: str
    messages: List[BaseMessage]
    output_message: BaseMessage
