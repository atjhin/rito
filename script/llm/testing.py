from .constants import Role
from .champions import ChampionBot, RoleAssignerBot, SummarizerBot, EventCreatorBot, NovelWriterBot
from typing import Optional, Set, List

from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, AIMessage

from .agent import Agent, AgentState, ModelConfig
from .constants import Role, ModelChoices
from dotenv import load_dotenv
import os


if __name__ == "__main__":
    aatrox = ChampionBot(Role.Aatrox, set("cheerful"))
    twisted_fate = ChampionBot(Role.TwistedFate, set("dark")) 
    initial_state = AgentState(messages=[AIMessage("Twisted Fate: Hey Ugly")])

    load_dotenv()
    google_model_config = ModelConfig(model=ModelChoices.gemini_2_5_flash_lite, provider="google_genai", api_key=os.getenv("GEMINI_API_KEY"))


    aatrox.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)
    aatrox.set_active_model(ModelChoices.gemini_2_5_flash_lite)
    twisted_fate.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)
    twisted_fate.set_active_model(ModelChoices.gemini_2_5_flash_lite)


    summarizer = SummarizerBot(Role.Summarizer, 6)
    event_creator = EventCreatorBot(Role.Event, [{"champion_name": "Twisted Fate", "personality": "dark"}, {"champion_name": "Aatrox", "personality": "cheerful"}], "Twisted Fate and Aatrox are computer science students. They are arguing about their group project.")
    role_assigner = RoleAssignerBot(Role.Role, ["Twisted Fate", "Aatrox"])
    novel_writer = NovelWriterBot(Role.Novel, 200, 500)

    summarizer.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)
    event_creator.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)
    role_assigner.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)
    novel_writer.register_model(ModelChoices.gemini_2_5_flash_lite, google_model_config)

    summarizer.set_active_model(ModelChoices.gemini_2_5_flash_lite)
    event_creator.set_active_model(ModelChoices.gemini_2_5_flash_lite)
    role_assigner.set_active_model(ModelChoices.gemini_2_5_flash_lite)
    novel_writer.set_active_model(ModelChoices.gemini_2_5_flash_lite)
    initial_state = AgentState(messages=[AIMessage(content="")])
    event_one = "Event 1: Twisted Fate's cynical insistence on a minimalist design clashes with Aatrox's boisterous vision for an overly complex, feature-rich group project."
    event_two = "Event 2: Their heated argument during a late-night coding session accidentally corrupts a critical module, jeopardizing their entire submission."
    event_three = "Event 3: A looming deadline forces the duo to grudgingly combine Twisted Fate's dark, meticulous debugging with Aatrox's cheerful, brute-force problem-solving."
    event_four = "Event 4: Twisted Fate uncovers a hidden, insidious bug planted by a rival student, prompting Aatrox to rally their focus for a counter-strategy."
    events = [event_one, event_two, event_three]
    
    initial_state = AgentState(messages=[AIMessage(content=event_one)])
    j = 0
    for i in range(800):
        next_player = role_assigner(initial_state)["ai_response"].content
        print(next_player)
        if next_player == "Twisted Fate":
            output = twisted_fate(initial_state)
            initial_state["messages"] = output["messages"]
        if next_player == "Aatrox":
            output = aatrox(initial_state)
            initial_state["messages"] = output["messages"]
        if next_player == "Event":
            j += 1
            if j == 3:
                break
            print("Event Triggered")
            initial_state["messages"] = initial_state["messages"] + [AIMessage(content=events[j])]
        initial_state = summarizer(initial_state)
    print(novel_writer(initial_state)["ai_response"].content)