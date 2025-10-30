from langgraph.graph import StateGraph, END
from typing import List

from .llm import *

# Assumed format
# [{"champion_name": "Zed",
#   "Personality": "Cheerful"},
# {"champion_name": "Twisted_fate",
#   "Personality": "Dark"}]

class StoryTeller():
    def __init__(self, input: List):
        graph = StateGraph(AgentState)
        self._preprocess_input(input)
        self._init_champions(list_of_champions)

    def _preprocess_input(self, input):
        self.champion_dict = {champ_dict['champion_name']: champ_dict['personality'] for champ_dict in input}

    def _init_champions(list_of_champions):
        dict_bots = {}
        for champ in list_of_champions:
            dict_bots[champ] = ChampionBot(Role[champ], )
            # tf = ChampionBot()
graph.add_node("RoleAssignerBot", RoleAssignerBot)
graph.add_node("EventCreatorBot", EventCreatorBot)
graph.add_node("NovelWriterBot", NovelWriterBot)
graph.add_node("SummarizerBot", SummarizerBot)

graph.add_edge("EventCreatorBot", "RoleAssignerBot")
graph.add_edge("tts", END)
graph.add_edge("llm", END)
graph.set_entry_point("llm")