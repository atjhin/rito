from typing import Optional, Set

from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base import Agent
from src.schemas.roles import Role
from src.schemas.state import AgentState
from src.core.lore import get_lore


class ChampionAgent(Agent):
    """Agent that roleplays as a specific League of Legends champion."""
    
    def __init__(
        self, role_name: Role, traits: Optional[Set[str]] = None, story_context: str = None
    ):
        self.traits = traits if traits is not None else set()
        self.story_context = story_context
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining the champion's personality,
        speaking style, and lore context.
        """
        prompt = """
        Imagine you are a script writer pretending to be {champion}, a champion from League of Legends. Your job 
        is to roleplay as {champion} and continue the script. Make sure you don't just repeat what your role did/said in the past.

        Your personality is {traits}.
        Below is your lore enclosed with triple backticks.
        ```
        {lore}
        ```

        DECISION ORDER
        1. Check the past conversations.
        2. Roleplay as {champion}, draft what you will say to continue the story. Make sure it fits the {champion} with personality and lore provided, and it is certain to progress the story.
        """
        lore = get_lore(self.role_name.value, story_context=self.story_context)
        
        # Debug print
        print(f"\n{'='*80}")
        print(f"Champion: {self.role_name.value}")
        print(f"Story Context: {self.story_context}")
        print(f"Summarized Lore:\n{lore}")
        print(f"{'='*80}\n")
        
        return SystemMessage(
            content=prompt.format(
                champion=self.role_name.value,
                traits=", ".join(self.traits),
                lore=lore,
            )
        )

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message representing the current turn of dialogue
        or event trigger for the champion.
        """
        prompt = """
        Continue the following script with dialogue and/or acting in 5 to 50 words. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.

        Make sure to use diverse vocabulary.
        Stick to your role.
        Do not repeat what your role said in the past.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name.value))

    def __call__(self, state: AgentState) -> AgentState:
        """Invoke call from base agent class."""
        output = super().__call__(state)
        return output

