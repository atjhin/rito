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

from constants import Role, ModelChoices


class AgentState(TypedDict, total=False):
    """Runtime state passed between graph nodes."""
    messages: List[BaseMessage]
    system_preset: Dict[Role, str]   # persona/system text per role
    human_message: Dict[Role, HumanMessage]
    lore: Dict[Role, str]            # optional lore per role (not used directly here)
    model: ModelChoices              # optional: requested model for this turn


class ModelConfig:
    """
    Configuration wrapper for initializing and caching chat models.

    Parameters
    ----------
    model : ModelChoices
        Model identifier (e.g., "gpt-4o", "claude-3-opus").
    provider : str
        Provider name ("openai", "anthropic", etc.).
    api_key : Optional[str]
        API key for the provider.
    temperature : float, default=0.7
        Sampling temperature for the model.
    kwargs : Optional[Dict[str, Any]]
        Additional keyword arguments passed to the model initializer.
    """

    def __init__(
        self,
        *,
        model: ModelChoices,
        provider: str,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.model = model.value
        self.provider = provider
        self.api_key = api_key
        self.temperature = temperature
        self.kwargs = kwargs or {}
        self._llm = None

    def get_llm(self):
        """
        Lazily initializes and returns the chat model instance.
        """
        if self._llm is None:
            self._llm = init_chat_model(
                model=self.model,
                model_provider=self.provider,
                api_key=self.api_key,
                temperature=self.temperature,
                **self.kwargs,
            )
        return self._llm


class Agent:
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

    def register_model(self, key: ModelChoices, cfg: ModelConfig):
        """
        Register a model configuration under a key.
        """
        self._models[key.value] = cfg

    def set_active_model(self, key: ModelChoices):
        """
        Set the currently active model.
        """
        if key.value not in self._models:
            raise KeyError(f"Unknown model key: {key}")
        self._active_model_key = key.value

    def add_tools(self, tools: List[BaseTool]):
        """
        Add LangChain-compatible tools to the agent.
        """
        self._tools.extend(tools)

    def __call__(self, state: AgentState) -> AgentState:
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

        messages_for_ai = [SystemMessage(content=state["system_preset"][self.role_name])] + state["messages"] + [state["human_message"][self.role_name]]
        
        ai = llm.invoke(messages_for_ai)
        return {"messages": state["messages"] + [ai]}
