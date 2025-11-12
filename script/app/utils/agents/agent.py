from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from app.utils.constants.models import ModelConfig
from app.utils.constants.roles import Role
from app.utils.data_models.agent_state import AgentState
from app.utils.data_models.agent_logger_item import AgentLoggerItem


from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.tools import BaseTool


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
        self.role_name = role_name  #
        self._models: Dict[str, ModelConfig] = {}
        self._active_model_key: Optional[str] = None
        self._tools: List[BaseTool] = []
        self._system_message = self._init_system_message()
        self._human_message = self._init_human_message()
        self.logger = None

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
        
        if self.logger is None: 
            raise RuntimeError("Logger instance not set.")
        
        llm = self._models[self._active_model_key].get_llm()
        
        if self._tools:
            llm = llm.bind_tools(self._tools)

        messages_for_ai = [self._system_message] + state["messages"] + [self._human_message]
        # self._log_llm_input(self._active_model_key, messages_for_ai)    

        ai = llm.invoke(messages_for_ai)

        self._log_llm_invocation(messages_for_ai, ai)

        # self._log_llm_output(ai)

        updated_message = state["messages"] + [ai] if add_to_state else state["messages"]

        return {"messages": updated_message, "ai_response": ai}
        # return {"messages": state["messages"] + [ai]} if add_to_state else {"messages": state["messages"]}

    def _log_llm_invocation(self, messages_for_ai: List[BaseMessage], ai: BaseMessage):
        """Logs the LLM invocation details using the Logger instance."""
        self.logger.log_llm_invocation(
                AgentLoggerItem(
                    agent_role_name=self.role_name.value,
                    model_name=self._active_model_key,
                    messages=messages_for_ai,
                    output_message=ai
                )
            )


    def _log_llm_input(self, model_key: str, input_messages: List[BaseMessage]):
        """Logs the model, prompt, and full context."""
        print(f"\n--- {self.role_name.value} Input Log ---")
        print(f"Model: {model_key}")
        print(f"Total Messages Sent: {len(input_messages)}")
        # Log the full context by converting messages to a printable format
        for msg in input_messages:
            print(f"  [{msg.type.upper()}]: {msg.content[:80]}...") # Print first 80 chars
        print(f"---------------------\n")

    def _log_llm_output(self, output_message: BaseMessage):
        """Logs the raw AI response."""
        print(f"\n--- {self.role_name.value} Output Log ---")
        print(f"AI Content: {output_message.content[:80]}...")
        if output_message.tool_calls:
            print(f"Tool Calls Detected: {len(output_message.tool_calls)}")
        # Log other metadata as needed, e.g., token usage from response_metadata
        print(f"----------------------\n")
