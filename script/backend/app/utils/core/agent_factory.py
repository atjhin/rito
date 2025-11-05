from app.utils.data_models.agent_creation_item import ChampionAgentConfig, EventCreatorAgentConfig, NovelWriterAgentConfig, RoleAssignerAgentConfig, SummarizerAgentConfig
from app.utils.agents.agent import Agent
from app.utils.agents.champion_agent import ChampionAgent
from app.utils.agents.event_creator_agent import EventCreatorAgent
from app.utils.agents.novel_writer_agent import NovelWriterAgent
from app.utils.agents.role_assigner_agent import RoleAssignerAgent
from app.utils.agents.summarizer_agent import SummarizerAgent


class AgentFactory:
    def __init__(self, agent_call_logger=None):
        self.agent_call_logger = agent_call_logger

    def create_champion_agent(self, config: ChampionAgentConfig) -> Agent:
        agent = ChampionAgent(
            role_name=config.role, # Role
            traits=config.traits # Set[str]
        )
        agent.register_model(
            config.model.model_name,
            config.model
        )
        agent.set_active_model(config.model.model_name)
        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
        return agent
    
    def create_event_creator_agent(self, config: EventCreatorAgentConfig) -> Agent:
        agent = EventCreatorAgent(
            role_name=config.role,
            champion_dict=config.input_json,
            scenario=config.scenario
        )
        agent.register_model(
            config.model.model_name,
            config.model
        )
        agent.set_active_model(config.model.model_name)

        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
        return agent
    
    def create_role_assigner_agent(self, config: RoleAssignerAgentConfig) -> Agent:
        agent = RoleAssignerAgent(
            role_name=config.role,
            champions_list=config.champions_list
        )
        agent.register_model(
            config.model.model_name,
            config.model
        )
        agent.set_active_model(config.model.model_name)

        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
        return agent
    
    def create_summarizer_agent(self, config: SummarizerAgentConfig) -> Agent:
        agent = SummarizerAgent(
            role_name=config.role,
        )
        agent.register_model(
            config.model.model_name,
            config.model
        )
        agent.set_active_model(config.model.model_name)

        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
        return agent
    
    def create_novel_writer_agent(self, config: NovelWriterAgentConfig) -> Agent:
        agent = NovelWriterAgent(
            role_name=config.role,
            min_words=config.min_words,
            max_words=config.max_words
        )
        agent.register_model(
            config.model.model_name,
            config.model
        )
        agent.set_active_model(config.model.model_name)
        if self.agent_call_logger:
            agent.logger = self.agent_call_logger
        return agent

