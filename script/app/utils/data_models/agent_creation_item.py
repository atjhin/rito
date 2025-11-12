from dataclasses import dataclass
from typing import List, Set, Any
from app.utils.constants.roles import Role
from enum import Enum
from app.utils.constants.models import ModelConfig

@dataclass
class BaseAgentConfig:
    """Parameters required by ALL agents."""

    role: Role
    model: ModelConfig


@dataclass
class ChampionAgentConfig(BaseAgentConfig):
    """Parameters required only by ChampionAgent."""

    traits: Set[str]


@dataclass
class EventCreatorAgentConfig(BaseAgentConfig):
    """Parameters required only by EventCreatorAgent."""

    input_json: List[Any]
    scenario: str


@dataclass
class RoleAssignerAgentConfig(BaseAgentConfig):
    """Parameters required only by RoleAssignerAgent."""

    champions_list: List[str]


@dataclass
class SummarizerAgentConfig(BaseAgentConfig):
    """Parameters required only by SummarizerAgent."""

    pass


@dataclass
class NovelWriterAgentConfig(BaseAgentConfig):
    """Parameters required only by NovelWriterAgent."""

    min_words: int
    max_words: int
