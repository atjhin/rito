from langgraph.graph import StateGraph, END
from typing import List

# from IPython.display import Image, display
from langchain_core.messages import AIMessage

from .llm import *


class StoryTeller:
    def __init__(self, scenario: str, input_json: List, log_file: str):
        # self.initial_state = AgentState(messages=[])
        self.graph = StateGraph(AgentState)
        self.scenario = scenario
        self.input_json = input_json
        self.logger = Logger(log_file=log_file)
        self._preprocess_input(input_json)
        self._init_champions()
        self.app = None


    def _preprocess_input(self, input_json):

        self.champion_dict = {
            champ_dict["name"]: (
                champ_dict["personality"],
                ModelChoices[champ_dict["models"]].value,
            )
            for champ_dict in input_json
        }

    def _init_champions(self):
        self.dict_bots = {}
        for champ_name, feature in self.champion_dict.items():
            personality, model = feature
            # print("\n\n\n")
            # print(model)
            # print("\n\n\n")
            self.dict_bots[champ_name] = ChampionBot(Role[champ_name], set(personality))


            self.dict_bots[champ_name].register_model(model.model_name, model)
            self.dict_bots[champ_name].set_active_model(model.model_name)
            self.dict_bots[champ_name].set_logger(self.logger)
            self.graph.add_node(champ_name, self.dict_bots[champ_name])

        # event_creator = EventCreatorBot(Role.Event, self.input_json, self.scenario)
        # event_creator.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)

    def build_graph(self):
        event_bot = EventCreatorBot(Role.Event, self.input_json, self.scenario)
        role_bot = RoleAssignerBot(Role.Role, self.champion_dict.keys())
        novel_bot = NovelWriterBot(Role.Novel, 200, 500)
        summarizer_bot = SummarizerBot(Role.Summarizer, 6)

        summarizer_bot.register_model("gemini-2.5-flash", ModelChoices.summarizer.value)
        event_bot.register_model("gemini-2.5-flash", ModelChoices.event.value)
        role_bot.register_model("gemini-2.5-flash", ModelChoices.role.value)
        novel_bot.register_model("gemini-2.5-flash", ModelChoices.novel.value)

        summarizer_bot.set_active_model("gemini-2.5-flash")
        event_bot.set_active_model("gemini-2.5-flash")
        role_bot.set_active_model("gemini-2.5-flash")
        novel_bot.set_active_model("gemini-2.5-flash")

        summarizer_bot.set_logger(self.logger)
        event_bot.set_logger(self.logger)
        role_bot.set_logger(self.logger)
        novel_bot.set_logger(self.logger)

        self.graph.add_node("RoleAssignerBot", role_bot)
        self.graph.add_node("EventCreatorBot", event_bot)
        self.graph.add_node("NovelWriterBot", novel_bot)
        self.graph.add_node("SummarizerBot", summarizer_bot)

        self.graph.set_entry_point("EventCreatorBot")
        self.graph.add_edge("EventCreatorBot", "RoleAssignerBot")

        self.graph.add_conditional_edges(
            "RoleAssignerBot",
            role_assigner_node,
            list(self.champion_dict.keys()) + ["NovelWriterBot", "RoleAssignerBot"],
        )
        for champ in self.champion_dict.keys():
            self.graph.add_edge(champ, "SummarizerBot")
            self.graph.add_edge("SummarizerBot", "RoleAssignerBot")
        self.graph.add_edge("NovelWriterBot", END)
        self.app = self.graph.compile()
        with open("graph.png", "wb") as f:
            f.write(self.app.get_graph().draw_mermaid_png())
        # display(Image(self.app.get_graph().draw_mermaid_png()))



    def invoke(self):
        self.app.invoke(
            AgentState(
                messages=[], model=None, next_bot=[], event_list=[], ai_response=""
            ),
            {"recursion_limit": 100},
        )
        self.logger.save_logs_to_file()
        self.logger.clear_logs()


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
        raise Exception("Something wrong lol")


if __name__ == "__main__":
    scenario = "Twisted Fate and Zed are computer science students. They are arguing about their group project."
    json_input = [
        {"name": "Zed", "personality": "Happy", "models": "gemini_2_5_flash_lite"},
        {
            "name": "TwistedFate",
            "personality": "Sad",
            "models": "gemini_2_5_flash_lite",
        },
    ]
    obj = StoryTeller(scenario=scenario, input_json=json_input, log_file="agent_log.json")
    obj.build_graph()
    print(obj.invoke())
# def append_event(self, state):
#     state['messages'].append()
