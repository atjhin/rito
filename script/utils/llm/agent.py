# agent.py
"""
Defines a flexible, personality-driven multi-model agent class built on LangChain.
This agent manages multiple LLM configurations, optional tool bindings, and model
switching. It's designed to be used as a node in a LangGraph app: the graph provides
state, and this node returns an updated state with the AI's reply appended.

Main components:
- ModelConfig: Wrapper for chat model initialization and configuration.
- AgentState: TypedDict defining the agent's message + model state.
- Agent: Callable node that consumes state and produces an updated state.

Intended usage:
- Persist personas/lore in graph state (or via a checkpointer).
- On each call, the agent prepends its role's system preset and invokes the LLM.
- If `model` is provided in state, the agent switches to that registered model.
"""

from typing import Dict, List, Optional, Any, TypedDict

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import BaseTool
from abc import ABC, abstractmethod
from collections import deque

from .constants import Role, ModelChoices, ModelConfig

class AgentState(TypedDict, total=False):
    """Runtime state passed between graph nodes."""
    messages: List[BaseMessage]
    # system_preset: Dict[Role, str]   # persona/system text per role
    # human_message: Dict[Role, HumanMessage]
    # lore: Dict[Role, str]            # optional lore per role (not used directly here)
    model: ModelChoices              # optional: requested model for this turn
    next_bot: List[str]
    event_list: List[str]
    ai_response: str


class Agent(ABC):
    """
    Callable agent node that maintains tools, switches models, and appends the AI reply.

    Attributes
    ----------
    role_name : Role
        The role/persona key this agent represents (used to select the system preset).
    _models : Dict[str, ModelConfig]
        Registered LLM configurations keyed by ModelChoices.value.
    _active_model_key : Optional[str]
        Key of the currently active model.
    _tools : List[BaseTool]
        LangChain-compatible tools available to the agent.
    """

    def __init__(self, role_name: Role):
        self.role_name = role_name
        self._models: Dict[str, ModelConfig] = {}
        self._active_model_key: Optional[str] = None
        self._tools: List[BaseTool] = []
        self._system_message = self._init_system_message()
        self._human_message = self._init_human_message()

        if not isinstance(self._system_message, SystemMessage):
            raise TypeError(
                f"{self.__class__.__name__}: _init_system_message() must return a SystemMessage, "
                f"got {type(self._system_message).__name__}"
            )

        if not isinstance(self._human_message, HumanMessage):
            raise TypeError(
                f"{self.__class__.__name__}: _init_human_message() must return a HumanMessage, "
                f"got {type(self._human_message).__name__}"
            )

    @abstractmethod
    def _init_system_message(self):
        pass

    @abstractmethod
    def _init_human_message(self):
        pass

    def register_model(self, key: str, cfg: ModelConfig):
        """
        Register a model configuration under a key.
        """
        self._models[key] = cfg

    def set_active_model(self, key: str):
        """
        Set the currently active model.
        """
        if key not in self._models:
            raise KeyError(f"Unknown model key: {key}")
        self._active_model_key = key

    def add_tools(self, tools: List[BaseTool]):
        """
        Add LangChain-compatible tools to the agent.
        """
        self._tools.extend(tools)

    def __call__(self, state: AgentState, add_to_state: bool = True) -> AgentState:
        """
        Execute an LLM call for the given state and return the updated state.
        - If `state.model` is provided, switch to that registered model.
        - Prepend this agent's role-specific system preset to the message history.
        - Append the AI response to `messages`.
        """
        if "model" in state and state["model"] is not None:
            self.set_active_model(state["model"])

        if self._active_model_key is None:
            raise RuntimeError("No active model set.")

        llm = self._models[self._active_model_key].get_llm()
        if self._tools:
            llm = llm.bind_tools(self._tools)

        messages_for_ai = [self._system_message] + state["messages"] + [self._human_message]
        
        ai = llm.invoke(messages_for_ai)
        # if add_to_state: state['messages'].append(ai)  
        # state['ai_response'] = [ai]
        # return state
        updated_message = state["messages"] + [ai] if add_to_state else state["messages"]
        return {"messages": updated_message, "ai_response": ai}
        # return {"messages": state["messages"] + [ai]} if add_to_state else {"messages": state["messages"]}
