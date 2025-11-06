from typing import List
from app.utils.constants.constants import Role
from app.utils.agents.agent import Agent
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.data_models.agent_state import AgentState


class RoleAssignerAgent(Agent):
    def __init__(self, role_name: Role, champions_list: List[str] = None):
        self.champions_list = champions_list
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
            - If the latest message is an event, DO NOT output `Event`.
            - If the latest 4 message is not an event, output an `Event`.
            
            ### Example
            Script:
            Event: A sudden storm causes a huge boulder to fall and forces the duel to pause.
            Zed: "Tch. Even the heavens try to interrupt me."
            Shen: "We shall continue this next time Zed. Until then be warned."

            Director output → Event   (because event is complete)
            """
        return SystemMessage(
            content=prompt.format(champions=", ".join(self.champions_list))
        )

    def _init_human_message(self) -> HumanMessage:
        """
        Returns the human message ...
        """
        prompt = """
        Based on the script above, determine which champion should go next or event.
        - Only output one of {champion_name}, Event.
        - Do not include any semicolons or colons
        """
        return HumanMessage(
            content=prompt.format(champion_name=", ".join(self.champions_list))
        )

    def __call__(self, state: AgentState) -> AgentState:
        """
        Invoke call from base agent class
        """
        next_bot = super().__call__(state, add_to_state=False)["ai_response"].content

        # have to make this more robust in the future
        next_bot = next_bot.replace(" ", "")

        state["next_bot"].append(next_bot)
        return state
