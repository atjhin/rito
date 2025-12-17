import os
from enum import Enum
from typing import Dict, Optional, Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model


load_dotenv()

# API keys for different providers
DICT_API = {
    "gemini": os.getenv("GOOGLE_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "xai": os.getenv("XAI_API_KEY"),
}

# Provider mapping for LangChain
DICT_PROVIDER = {
    "gemini": "google_genai",
    "openai": "openai",
    "xai": "xai",
}


class ModelConfig:
    """
    Configuration wrapper for initializing and caching chat models.

    Parameters
    ----------
    model_name : str
        Model identifier (e.g., "gemini-2.0-flash-lite", "gpt-4o").
    model_family : str
        Provider family name ("gemini", "openai", "xai").
    temperature : float, default=0.7
        Sampling temperature for the model.
    kwargs : Optional[Dict[str, Any]]
        Additional keyword arguments passed to the model initializer.
    """

    def __init__(
        self,
        model_name: str,
        model_family: str,
        temperature: float = 0.7,
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.model_name = model_name
        self.model_family = model_family
        self.temperature = temperature
        self.kwargs = kwargs or {}
        self._llm = None
        self.provider = DICT_PROVIDER[self.model_family]
        self.api_key = DICT_API[self.model_family]

    def get_llm(self):
        """Lazily initializes and returns the chat model instance."""
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
    """Available LLM model configurations."""
    
    # General purpose models
    gemini_2_0_flash_lite = ModelConfig("gemini-2.0-flash-lite", "gemini")
    gemini_2_5_flash_lite = ModelConfig("gemini-2.5-flash-lite", "gemini")
    gemini_2_5_flash = ModelConfig("gemini-2.5-flash", "gemini")
    grok_4 = ModelConfig("grok-4", "xai")
    gpt_4o_mini = ModelConfig("gpt-4o-mini", "openai")
    gpt_4o = ModelConfig("gpt-4o", "openai")
    
    # Role-specific model assignments
    Summarizer = ModelConfig("grok-4", "xai")
    Event = ModelConfig("grok-4", "xai")
    Novel = ModelConfig("grok-4", "xai")
    RoleAssigner = ModelConfig("gpt-4o-mini", "openai")

