from app.utils.core.agent_factory import AgentFactory
from app.utils.data_models.agent_creation_item import (
    ChampionAgentConfig,
    EventCreatorAgentConfig,
    NovelWriterAgentConfig,
    RoleAssignerAgentConfig,
    SummarizerAgentConfig,
)
from langgraph.graph import StateGraph, END
from app.utils.constants.roles import Role
from app.utils.constants.models import ModelChoices
from app.utils.constants.path_config import Config
from app.utils.data_models.agent_state import AgentState
from langchain_core.messages import AIMessage
from app.utils.data_models.story_teller_item import StoryTellerItem
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import os


class StoryTeller:
    def __init__(self, scenario, champions_json, logger):
        self.graph = StateGraph(AgentState)
        self.scenario = scenario
        self.champions_json = champions_json
        self.logger = logger
        self.agent_factory = AgentFactory()
        self._preprocess_input()
        self.conn = None
        self.app = None
        self.db_path = Config.LANGGRAPH_CHECKPOINTS_DB

    def __init__(self, story_teller_item: StoryTellerItem):
        self.graph = StateGraph(AgentState)
        self.scenario = story_teller_item.scenario
        self.champions_json = story_teller_item.champions
        self.logger = story_teller_item.logger
        self.agent_factory = AgentFactory()
        self._preprocess_input()
        self.conn = None
        self.app = None
        self.db_path = Config.LANGGRAPH_CHECKPOINTS_DB

    def _preprocess_input(self):
        self.champion_agents = {}
        for champ in self.champions_json:
            champ_name = champ["name"]
            champ_traits = set(champ["personality"])
            champ_model = ModelChoices[champ["models"]]
            champ_agent_config = ChampionAgentConfig(
                role=Role[champ_name],
                model=champ_model,
                traits=champ_traits,
                story_context=self.scenario,
            )
            self.champion_agents[champ_name] = self.agent_factory.create_champion_agent(
                champ_agent_config
            )
            self.graph.add_node(champ_name, self.champion_agents[champ_name])

    def build_graph(self):
        event_bot = self.agent_factory.create_event_creator_agent(
            EventCreatorAgentConfig(
                role=Role.Event,
                model=ModelChoices.Event,
                input_json=self.champions_json,
                scenario=self.scenario,
            )
        )
        role_bot = self.agent_factory.create_role_assigner_agent(
            RoleAssignerAgentConfig(
                role=Role.RoleAssigner,
                model=ModelChoices.RoleAssigner,
                champions_list=list(self.champion_agents.keys()),
            )
        )
        summarizer_bot = self.agent_factory.create_summarizer_agent(
            SummarizerAgentConfig(role=Role.Summarizer, model=ModelChoices.Summarizer)
        )
        novel_bot = self.agent_factory.create_novel_writer_agent(
            NovelWriterAgentConfig(
                role=Role.Novel,
                model=ModelChoices.Novel,
                min_words=200,
                max_words=500,
            )
        )

        self.graph.add_node("RoleAssignerBot", role_bot)
        self.graph.add_node("EventCreatorBot", event_bot)
        self.graph.add_node("NovelWriterBot", novel_bot)
        self.graph.add_node("SummarizerBot", summarizer_bot)

        self.graph.set_entry_point("EventCreatorBot")
        self.graph.add_edge("EventCreatorBot", "RoleAssignerBot")

        self.graph.add_conditional_edges(
            "RoleAssignerBot",
            role_assigner_node,
            list(self.champion_agents.keys()) + ["NovelWriterBot", "RoleAssignerBot"],
        )
        for champ in self.champion_agents.keys():
            self.graph.add_edge(champ, "SummarizerBot")
            self.graph.add_edge("SummarizerBot", "RoleAssignerBot")
        self.graph.add_edge("NovelWriterBot", END)

        print(f"\n{'='*60}")
        print(f"DB path: {self.db_path}")
        print(f"{'='*60}\n")

        # Use config path
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        memory = SqliteSaver(self.conn)
        self.app = self.graph.compile(checkpointer=memory)

        # Save graph visualization using config path
        try:
            with open(str(Config.GRAPH_VISUALIZATION_PATH), "wb") as f:
                f.write(self.app.get_graph().draw_mermaid_png())
            print(f"Graph visualization saved to {Config.GRAPH_VISUALIZATION_PATH}\n")
        except Exception as e:
            print(f"Warning: Could not save graph visualization: {e}\n")

    def invoke(self):
        thread_id = "session_1"
        config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}

        result = self.app.invoke(
            AgentState(
                messages=[], model=None, next_bot=[], event_list=[], ai_response=""
            ),
            config,
        )
        if self.conn:
            self.conn.commit()
            self.conn.close()

        try:
            self.logger.export_and_save_checkpoints_to_s3(self.db_path)
            self.logger._cleanup_database(self.db_path)
        except Exception as e:
            raise

        # serializable_result = {
        #     'ai_response': result.get('ai_response', ''),
        #     'messages': [
        #         {
        #             'role': getattr(msg, 'type', 'unknown'),
        #             'content': msg.content if hasattr(msg, 'content') else str(msg)
        #         }
        #         for msg in result.get('messages', [])
        #     ],
        #     'event_list': list(result.get('event_list', [])),
        #     'next_bot': result.get('next_bot', []),
        #     'model': str(result.get('model', '')) if result.get('model') else None
        # }

        # get the content of ai_response
        return result["ai_response"].content


def role_assigner_node(state):
    if len(state["next_bot"]) > 0:
        next_bot = state["next_bot"][-1]
        if (next_bot == "Event") and (len(state["event_list"]) == 0):
            return "NovelWriterBot"
        elif next_bot == "Event":
            next_event = state["event_list"].popleft()
            state["messages"].append(AIMessage(content=next_event))
            return "RoleAssignerBot"
        else:
            return next_bot
    else:
        raise Exception("Something wrong")


if __name__ == "__main__":
    from .logger import Logger

    scenario = "Twisted Fate and Zed are computer science students. They are arguing about their group project."
    json_input = [
        {"name": "Zed", "personality": "Happy", "models": "gemini_2_0_flash_lite"},
        {
            "name": "TwistedFate",
            "personality": "Sad",
            "models": "gemini_2_0_flash_lite",
        },
    ]
    logger = Logger()
    story_teller = StoryTeller(
        scenario=scenario, champions_json=json_input, logger=logger
    )
    assert story_teller is not None
    story_teller.build_graph()
    print(story_teller.invoke())
