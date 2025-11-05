from app.utils.data_models.agent_creation_item import (
    ChampionAgentConfig, EventCreatorAgentConfig, NovelWriterAgentConfig, 
    RoleAssignerAgentConfig, SummarizerAgentConfig, BaseAgentConfig # Assuming a BaseConfig exists
)
from app.utils.agents.agent import Agent
from app.utils.agents.champion_agent import ChampionAgent
from app.utils.agents.event_creator_agent import EventCreatorAgent
from app.utils.agents.novel_writer_agent import NovelWriterAgent
from app.utils.agents.role_assigner_agent import RoleAssignerAgent
from app.utils.agents.summarizer_agent import SummarizerAgent
from typing import Any # Use Any for config if BaseAgentConfig isn't defined


class AgentFactory:
    def __init__(self, agent_call_logger=None):
        self.agent_call_logger = agent_call_logger

    def _configure_agent(self, agent: Agent, config: Any) -> Agent:
        """
        Private helper method to handle common agent configuration steps:
        1. Model registration and activation.
        2. Logger injection.
        """
        # 1. Model Configuration
        model_key = config.model.model_name
        agent.register_model(model_key, config.model)
        agent.set_active_model(model_key)
        
        # 2. Logger Injection
        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
            
        return agent

    def create_champion_agent(self, config: ChampionAgentConfig) -> Agent:
        """Creates a ChampionAgent and applies common setup."""
        agent = ChampionAgent(
            role_name=config.role,
            traits=config.traits
        )
        # Use the helper method for common steps
        return self._configure_agent(agent, config)
    
    def create_event_creator_agent(self, config: EventCreatorAgentConfig) -> Agent:
        """Creates an EventCreatorAgent and applies common setup."""
        agent = EventCreatorAgent(
            role_name=config.role,
            champion_dict=config.input_json,
            scenario=config.scenario
        )
        # Use the helper method for common steps
        return self._configure_agent(agent, config)
    
    def create_role_assigner_agent(self, config: RoleAssignerAgentConfig) -> Agent:
        """Creates a RoleAssignerAgent and applies common setup."""
        agent = RoleAssignerAgent(
            role_name=config.role,
            champions_list=config.champions_list
        )
        # Use the helper method for common steps
        return self._configure_agent(agent, config)
    
    def create_summarizer_agent(self, config: SummarizerAgentConfig) -> Agent:
        """Creates a SummarizerAgent and applies common setup."""
        agent = SummarizerAgent(
            role_name=config.role,
        )
        # Use the helper method for common steps
        return self._configure_agent(agent, config)
    
    def create_novel_writer_agent(self, config: NovelWriterAgentConfig) -> Agent:
        """Creates a NovelWriterAgent and applies common setup."""
        agent = NovelWriterAgent(
            role_name=config.role,
            min_words=config.min_words,
            max_words=config.max_words
        )
        # Use the helper method for common steps
        return self._configure_agent(agent, config)