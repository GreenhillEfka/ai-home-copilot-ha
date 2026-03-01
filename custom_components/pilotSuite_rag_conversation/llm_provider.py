"""Base LLM Provider Interface for PilotSuite RAG Conversation."""

from abc import ABC, abstractmethod
import logging
from typing import Optional

_LOGGER = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, name: str, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the base provider.
        
        Args:
            name: Provider name for logging purposes
            base_url: Base URL for the API endpoint
            api_key: API key for authentication (if required)
            model: Model name/identifier to use
        """
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self._timeout_seconds = 30

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.
        
        Args:
            prompt: The input prompt to generate a response for
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If generation fails
        """
        pass

    async def _log_success(self, prompt_length: int, response_length: int) -> None:
        """Log successful generation.
        
        Args:
            prompt_length: Length of the input prompt
            response_length: Length of the generated response
        """
        _LOGGER.info(
            f"[{self.name}] Generation successful - prompt: {prompt_length} chars, "
            f"response: {response_length} chars"
        )

    async def _log_error(self, error: Exception) -> None:
        """Log generation error.
        
        Args:
            error: The exception that occurred
        """
        _LOGGER.error(f"[{self.name}] Generation failed: {error}")
