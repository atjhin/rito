from typing import List
from app.utils.constants.roles import Role
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
        is a list of champions with their personalities.

        Champions
        {champion_desc}

        You will receive a short starting scenario written by the user. That scenario is the beginning of the story.

        Your job is to expand this starting plot into a **complete storyline** by generating a small sequence of engaging events that:
        - feel like direct continuations of the scenario (no hard resets or unrelated scenes),
        - stay within the same general setting, tone, and time frame unless the scenario clearly suggests a change,
        - remain consistent with the champions' personalities and the world of League of Legends.

        Rules:
        - Write the output as a **numbered list of events** (e.g., "Event 1: ...", "Event 2: ...").
        - Each event should be **1-2 sentences**, around 20-40 words.
        - Always prefix with "Event X: <description>".
        - Ensure the events form a coherent **beginning → middle → climax → resolution** that grows naturally from the scenario.
        - Do NOT contradict or rewrite facts already established in the scenario.
        - Never output nothing. If unsure, choose the most plausible next event that respects the scenario and champion traits.
        - Make sure to use information from the scenario provided below as the foundation for all events.

        Example format:
        Event 1: A sudden interruption forces the group to change plans and test their priorities.
        Event 2: One champion proposes a risky idea that creates tension and pushes the story forward.

        DECISION ORDER:
        1. Create events that follow logically from the scenario and obey the rules.
        2. Use as few events as possible while keeping the story interesting (2-5 total).
        3. Output the list of events while adhering to the Example format.
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
        Given the scenario below, produce a concise list of interesting story events that **continue naturally** from it.

        The scenario is the beginning of the story. Your events must:
        - logically follow from what has already happened in the scenario,
        - avoid large, unexplained jumps in location, stakes, or tone,
        - keep existing details, relationships, and motivations consistent,
        - stay within the same general situation unless the scenario clearly hints at a change.

        The number of events is bounded between 2 and 5.
        Make sure the events are meaningful, connected, and move the plot forward.

        Scenario:
        {scenario}

        Instructions:
        - Decide the number of events internally (do not output the decision line).
        - Then output the event list in the format below.
        - Keep events minimal, focused, and connected.
        - Do NOT write the full story — only outline the events.
        - Do NOT restate the scenario; focus on what happens next.
        - Make the events interesting and dynamic.

        Output Format:
        Event 1: <1-2 sentence plot event>
        Event 2: <1-2 sentence plot event>
        Event 3: ...
        ...
        """

        return HumanMessage(
            content=prompt.format(champion=self.role_name.value, scenario=self.scenario)
        )

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        output = super().__call__(state, add_to_state=False)

        event_list = deque(output["ai_response"].content.split("\n"))
        next_event = event_list.popleft()
        output["event_list"] = event_list
        output["messages"].append(AIMessage(content=f"Event: {next_event}"))
        return output
