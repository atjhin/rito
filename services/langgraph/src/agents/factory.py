from typing import Any

from src.agents.base import Agent
from src.agents.champion import ChampionAgent
from src.agents.event_creator import EventCreatorAgent
from src.agents.novel_writer import NovelWriterAgent
from src.agents.role_assigner import RoleAssignerAgent
from src.agents.summarizer import SummarizerAgent
from src.schemas.agent_config import (
    ChampionAgentConfig,
    EventCreatorAgentConfig,
    NovelWriterAgentConfig,
    RoleAssignerAgentConfig,
    SummarizerAgentConfig,
)


class AgentFactory:
    """Factory for creating and configuring agents."""

    def __init__(self):
        pass

    def _configure_agent(self, agent: Agent, config: Any) -> Agent:
        """
        Private helper method to handle common agent configuration steps:
        1. Model registration and activation.
        """
        model_key = config.model.value.model_name
        agent.register_model(model_key, config.model.value)
        agent.set_active_model(model_key)
        return agent

    def create_champion_agent(self, config: ChampionAgentConfig) -> Agent:
        """Creates a ChampionAgent and applies common setup."""
        story_context = getattr(config, "story_context", None)
        agent = ChampionAgent(
            role_name=config.role,
            traits=config.traits,
            story_context=story_context,
        )
        return self._configure_agent(agent, config)

    def create_event_creator_agent(self, config: EventCreatorAgentConfig) -> Agent:
        """Creates an EventCreatorAgent and applies common setup."""
        agent = EventCreatorAgent(
            role_name=config.role,
            champion_dict=config.input_json,
            scenario=config.scenario,
        )
        return self._configure_agent(agent, config)

    def create_role_assigner_agent(self, config: RoleAssignerAgentConfig) -> Agent:
        """Creates a RoleAssignerAgent and applies common setup."""
        agent = RoleAssignerAgent(
            role_name=config.role,
            champions_list=config.champions_list,
        )
        return self._configure_agent(agent, config)

    def create_summarizer_agent(self, config: SummarizerAgentConfig) -> Agent:
        """Creates a SummarizerAgent and applies common setup."""
        agent = SummarizerAgent(role_name=config.role)
        return self._configure_agent(agent, config)

    def create_novel_writer_agent(self, config: NovelWriterAgentConfig) -> Agent:
        """Creates a NovelWriterAgent and applies common setup."""
        agent = NovelWriterAgent(
            role_name=config.role,
            min_words=config.min_words,
            max_words=config.max_words,
        )
        return self._configure_agent(agent, config)

