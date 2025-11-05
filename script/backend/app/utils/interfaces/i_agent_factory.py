
from abc import ABC, abstractmethod

class IAgentFactory(ABC):
    @abstractmethod
    def create_agent(self, config: 'AgentConfig') -> 'Agent':
        """
        Create and return an agent instance based on the provided configuration.

        Parameters
        ----------
        config : AgentConfig
            Configuration object containing parameters needed to create the agent.

        Returns
        -------
        Agent
            An instance of the created agent.
        """
        pass
