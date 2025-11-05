from typing import List
from app.utils.constants.constants import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.utils.data_models.agent_state import AgentState
from collections import deque


class EventCreatorAgent(Agent):
    def __init__(self, role_name: Role, champion_dict: List[str], scenario: str):
        self.champion_dict = champion_dict
        self.scenario = scenario
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
        return SystemMessage(
            content=prompt.format(
                champion_desc="\n".join(
                    f"{c['name']}: {c['personality']}," for c in self.champion_dict
                )
            )
        )

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Given the scenario below, use it as a basis to create the list of 4 events. If the scenario is incomplete or missing, complete it with creativity.

        Scenario: 
        {scenario}
        """
        return HumanMessage(
            content=prompt.format(champion=self.role_name.value, scenario=self.scenario)
        )

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        # print(state)
        # Reuse the base Agent call, to be deleted if no additional change is required.
        output = super().__call__(state, add_to_state=False)
        event_list = deque(output["ai_response"].content.split("\n"))
        next_event = event_list.popleft()
        output["event_list"] = event_list
        output["messages"].append(AIMessage(content=f"Event: {next_event}"))
        return output
