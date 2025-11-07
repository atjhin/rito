import os
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict
from dotenv import load_dotenv

from langchain.chat_models import init_chat_model

base_dir = os.path.dirname(__file__)
champions_path = os.path.join(base_dir, "champions.txt")

class Role(Enum):
    def __new__(cls, display_name: str, temperature: float):
        obj = object.__new__(cls)
        obj._value_ = display_name  
        obj.temperature = temperature
        return obj

roles = {}
with open("utils/champions.txt") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, temp = line.rsplit(" ", 1)
        identifier = (
            name.replace(" ", "")
                .replace("'", "")
                .replace(".", "")
                .replace("&", "And")
        )
        roles[identifier] = name

Role = Enum("Role", roles, type=Role)
load_dotenv()

DICT_API = {
    'gemini': os.getenv("GOOGLE_API_KEY")
}

DICT_PROVIDER ={
    'gemini': "google_genai"
}

class ModelConfig:
    """
    Configuration wrapper for initializing and caching chat models.

    Parameters
    ----------
    model : ModelChoices
        Model identifier (e.g., "gpt-4o", "claude-3-opus").
    provider : str
        Provider name ("openai", "anthropic", etc.).
    api_key : Optional[str]
        API key for the provider.
    temperature : float, default=0.7
        Sampling temperature for the model.
    kwargs : Optional[Dict[str, Any]]
        Additional keyword arguments passed to the model initializer.
    """

    def __init__(
        self,
        # *,
        model_name: str,
        model_family: str,
        # provider: str,
        # api_key: Optional[str] = None,
        temperature: float = 0.7,
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.model_family = model_family
        # self.provider = provider
        # self.api_key = api_key
        self.temperature = temperature
        self.kwargs = kwargs or {}
        self._llm = None
        self.provider = DICT_PROVIDER[self.model_family]
        self.api_key = DICT_API[self.model_family]

    def get_llm(self):
        """
        Lazily initializes and returns the chat model instance.
        """
        if self._llm is None:
            self._llm = init_chat_model(
                model=self.model_name,
                model_provider=self.provider,
                api_key=self.api_key,
                temperature=self.temperature,
                **self.kwargs,
            )
        return self._llm


class ModelChoices(Enum):
    gemini_2_flash_lite = ModelConfig("gemini-2.0-flash-lite", "gemini")
    gemini_2_5_flash_lite = ModelConfig("gemini-2.5-flash-lite", "gemini")
    gemini_2_5_flash = ModelConfig("gemini-2.5-flash", "gemini")
    summarizer = ModelConfig("gemini-2.0-flash-lite", "gemini")
    event = ModelConfig("gemini-2.0-flash-lite", "gemini")
    novel = ModelConfig("gemini-2.0-flash-lite", "gemini")
    role = ModelConfig("gemini-2.0-flash-lite", "gemini")
    # event_creator = ModelConfig("gemini-2.5-flash-lite", "gemini")
