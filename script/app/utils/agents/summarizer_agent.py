from typing import List
from app.utils.constants.roles import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from app.utils.data_models.agent_state import AgentState


class SummarizerAgent(Agent):
    """
    Summarizes earlier conversation and rewrites state['messages'] as:
      [System(running memory)] + last_k_messages

    Notes:
    - Uses the currently active model registered on this Agent (via register_model / set_active_model).
    - Does NOT append its own AI message to the transcript; instead it compresses and replaces history.
    """

    def __init__(
        self,
        role_name: Role,
        k_keep: int = 8,
    ):
        self.k_keep = max(0, int(k_keep))
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the memory compression task.
        """
        prompt = """
        You are a memory compressor for a multi-character roleplay. Produce a concise running memory preserving: (1) key plot facts, (2) each speaker's intentions, (3) unresolved threads, and (4) world-state changes and commitments. Keep names consistent. Do not invent new facts. Aim ~120–200 words.
        """
        return SystemMessage(content=prompt)

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message defining the summarization input format.
        """
        prompt = """
       Given the earlier conversation above, produce a summary with the following Output format:
        1) Short paragraph summary (3-6 sentences).
        2) Bulleted 'open threads' checklist, if any (<=5 bullets).
        """
        return HumanMessage(content=prompt)

    def __call__(self, state: AgentState) -> AgentState:
        """
        Compress older history into a single SystemMessage + keep last k messages.
        Rewrites state['messages'] and returns updated state.
        """
        messages: List[BaseMessage] = state.get("messages", [])
        if not messages or len(messages) <= self.k_keep:
            # Nothing to compress; pass through unchanged
            return state

        print("\n Summarization Happened\n")

        head = messages[: -self.k_keep // 2]
        tail = messages[-self.k_keep // 2 :]

        # Get active LLM from the Agent's registry
        if self._active_model_key is None:
            raise RuntimeError(
                "SummarizerBot: no active model set. Call register_model() and set_active_model()."
            )
        llm = self._models[self._active_model_key].get_llm()

        messages_for_ai = [self._system_message] + head + [self._human_message] #!

        summary = llm.invoke(messages_for_ai)

        state["messages"] = [summary] + tail
        return state
