import os
from enum import Enum
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from pathlib import Path
from langchain.chat_models import init_chat_model

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
    gemini_2_0_flash_lite = ModelConfig("gemini-2.0-flash-lite", "gemini")
    gemini_2_5_flash_lite = ModelConfig("gemini-2.5-flash-lite", "gemini")
    gemini_2_5_flash = ModelConfig("gemini-2.5-flash", "gemini")
    Summarizer = ModelConfig("gemini-2.5-flash", "gemini")
    Event = ModelConfig("gemini-2.5-flash-lite", "gemini")
    Novel = ModelConfig("gemini-2.5-flash-lite", "gemini")
    RoleAssigner = ModelConfig("gemini-2.5-flash-lite", "gemini")
