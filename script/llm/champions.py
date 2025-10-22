from typing import Optional, Set, List

from langchain_core.messages import SystemMessage, HumanMessage

from .agent import Agent, AgentState
from .constants import Role
# from .prompts import CHAMPION_SYSTEM_PROMPT, CHAMPION_REPLY_PROMPT


class ChampionBot(Agent):
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
            League of Legend universe based on a particular scenario. Below is your lore enclosed with triple backticks.
            ```
            {lore}
            ```
            """
        lore = get_lore(self.role_name) # To be defined
        return SystemMessage(content=prompt.format(champion=self.role_name, lore=lore))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message representing the current turn of dialogue
        or event trigger for the champion.
        """
        prompt = """
        Continue the following script by answering the dialogue and/or acting. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.
            - If you are unsure, improvise.
            - Follow the script's latest event and improvise.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class 
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state)





class RoleAssignerBot(Agent):
    def __init__(self, role_name: Role, champions_ls: List[str] = None):
        self.champions_ls = champions_ls
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining ...
        """
        prompt = """
            Imagine you are a **script director** for a League of Legends roleplay.  
            Your sole responsibility is to decide **which champion should speak next OR when to trigger a new event**.  

            Output options: ({champions}), Event)

            Rules:
            - Only output one of the following: a champion's name () or `Event`.  
            - If the **current event is still unfolding**, continue passing turns between champions so they can react.
            - If the current event has been played out by the actors, output `Event` to signal the next event.
            - If the conversation stalls, output `Event` to signal the next event.  
            - Always encourage natural turn-taking between champions.  
            - Never output dialogue, only the next speaker or `Event`.  
            
            ### Example
            Script:
            Event: A sudden storm causes a huge boulder to fall and forces the duel to pause.
            Zed: "Tch. Even the heavens try to interrupt me."
            Shen: "We shall continue this next time Zed. Until then be warned."

            Director output → Event   (because event is complete)
            """
        return SystemMessage(content=prompt.format(champions=', '.join(self.champions_ls)))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Continue the following script by answering the dialogue and/or acting. FOLLOW THE RULES BELOW
            - Always prefix your response with {champion}: <answer>. 
            - Never remain silent.
            - All act should be enclosed with brackets.
            - If you are unsure, improvise.
            - Follow the script's latest event and improvise.
        """
        return HumanMessage(content=prompt.format(champion=self.role_name))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state, add_to_state=False)


class EventCreatorBot(Agent):
    def __init__(self, role_name: Role, champion_dict: List[str] = None):
        self.champion_dict = champion_dict
        super().__init__(role_name)

    def _init_system_message(self) -> SystemMessage:
        """
        Returns the system prompt defining ...
        """
        prompt = """
            Imagine you are an event creator working as a script writer for a League of Legends roleplay. Below
            is a list of dictionary where the name and the personalities for each league of legend champion is provided.
            Champions
            {champion_desc}

            Your job is to expand the starting plot into a **complete storyline** by generating a sequence of engaging events.  
            Each event should naturally follow the previous one, encourage interactions, and stay consistent with the champions'
            personalities and the world of League of Legends.

            Rules:
            - Write the output as a **numbered list of events** (e.g., "Event 1: ...", "Event 2: ...").  
            - Each event should be **1-2 sentences**, around 20-40 words.  
            - Always prefix with "Event X: <description>".  
            - Keep events action-oriented and dynamic (conflict, alliance, discovery, danger, resolution).  
            - Ensure the events form a coherent **beginning → middle → climax → resolution** plot arc.  
            - Never output nothing. If unsure, improvise while staying consistent with the champions and their traits.  
            - Make sure to use information from the scenario provided below.

            Example format:
            Event 1: A sudden storm forces the group into an uneasy alliance.  
            Event 2: Zed suggests a dangerous shortcut, testing Shen's cautious nature.  
            """
        return SystemMessage(content=prompt.format(champion_desc="\n".join(f"{c['champion_name']}: {c['personality']}," for c in self.champion_dict)))

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Given the scenario below, use it as a basis to create the list of events. If the scenario is incomplete or missing, complete it with creativity.

        Scenario: 
        """
        return HumanMessage(content=prompt.format(champion=self.role_name))


    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # Reuse the base Agent call, to be deleted if no additional change is required.
        return super().__call__(state, add_to_state=False)