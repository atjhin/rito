from typing import Optional, Set
from app.utils.constants.constants import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.data_models.agent_state import AgentState
from app.utils.constants.champion_lore import (
    get_lore,
)

class ChampionAgent(Agent):
    def __init__(self, role_name: Role, traits: Optional[Set[str]] = None):
        self.traits = traits if traits is not None else set()
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the champion's personality,
        speaking style, and lore context. This stays consistent for this agent.
        """
        prompt = """
            Imagine you are a script writer pretending to be {champion}, a champion from League of Legends. Your job 
            is to roleplay as {champion} and continue the script as you interact with different champions in the 
            League of Legend universe based on a particular scenario. 
            Your personality is {traits}
            Below is your lore enclosed with triple backticks.
            ```
            {lore}
            ```
            """
        lore = get_lore(self.role_name.value)  # To be defined
        print(f"Fetched lore for {self.role_name.value}: {lore[:60]}...")  # Debug print
        return SystemMessage(
            content=prompt.format(
                champion=self.role_name.value, traits=", ".join(self.traits), lore=lore
            )
        )

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message representing the current turn of dialogue
        or event trigger for the champion.
        """
        prompt = """
        Continue the following script by answering the dialogue and/or acting in 5 to 50 words. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.
            - If you are unsure, improvise.
            - Follow the script's latest event and improvise.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name.value))

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        output = super().__call__(state)
        return output
