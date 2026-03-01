"""LLM Fallback Chain for automatic provider failover."""

import asyncio
import logging
from typing import List, Optional
from dataclasses import dataclass, field

try:
    from .llm_provider import BaseLLMProvider
    from .providers import OpenAIProvider, OllamaProvider, OllamaTinyProvider
except ImportError:
    from llm_provider import BaseLLMProvider
    from providers import OpenAIProvider, OllamaProvider, OllamaTinyProvider

_LOGGER = logging.getLogger(__name__)


@dataclass
class FallbackConfig:
    """Configuration for LLM fallback chain."""
    fallback_enabled: bool = True
    fallback_order: List[str] = field(default_factory=lambda: ["openai", "ollama", "ollama_tiny"])
    provider: str = "openai"
    openai_api_key: Optional[str] = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5"
    ollama_tiny_model: str = "qwen3.5:7b"
    timeout_seconds: int = 30


class LLMFallbackChain:
    """
    LLM Fallback Chain that automatically tries providers in configured order.
    
    On timeout or error, automatically falls back to the next provider in the chain.
    Logs which provider was successful. Raises exception if ALL providers fail.
    """

    def __init__(self, config: FallbackConfig):
        """Initialize the fallback chain.
        
        Args:
            config: FallbackConfig with provider settings and order
        """
        self.config = config
        self.providers: List[BaseLLMProvider] = []
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize provider instances based on configuration."""
        provider_map = {
            "openai": OpenAIProvider(
                api_key=self.config.openai_api_key or "",
                model=self.config.provider,
                timeout_seconds=self.config.timeout_seconds,
            ),
            "ollama": OllamaProvider(
                base_url=self.config.ollama_url,
                model=self.config.ollama_model,
                timeout_seconds=self.config.timeout_seconds,
            ),
            "ollama_tiny": OllamaProvider(
                base_url=self.config.ollama_url,
                model=self.config.ollama_tiny_model,
                timeout_seconds=self.config.timeout_seconds,
            ),
        }

        for provider_name in self.config.fallback_order:
            if provider_name in provider_map:
                self.providers.append(provider_map[provider_name])
                _LOGGER.debug("[FallbackChain] Initialized provider: %s", provider_name)
            else:
                _LOGGER.warning("[FallbackChain] Unknown provider in fallback_order: %s", provider_name)

        if not self.providers:
            raise ValueError("No valid providers configured in fallback_order")

        _LOGGER.info(
            "[FallbackChain] Initialized with %d providers: %s",
            len(self.providers),
            self.config.fallback_order
        )

    async def generate(self, prompt: str) -> str:
        """
        Generate a response using the fallback chain.
        
        Tries providers in configured order (fallback_order).
        On timeout or error, automatically tries the next provider.
        Logs which provider succeeded.
        Raises exception if ALL providers fail.
        
        Args:
            prompt: The input prompt to generate a response for
            
        Returns:
            The generated response text from the first successful provider
            
        Raises:
            Exception: If all providers fail
        """
        if not self.config.fallback_enabled:
            # Fallback disabled, use only the first provider
            if not self.providers:
                raise ValueError("No providers available")
            return await self._try_provider(self.providers[0], prompt)

        last_error: Optional[Exception] = None
        
        for i, provider in enumerate(self.providers):
            provider_name = provider.name
            attempt = i + 1
            total = len(self.providers)
            
            _LOGGER.debug(
                "[FallbackChain] Attempt %d/%d: Trying provider '%s'",
                attempt, total, provider_name
            )
            
            try:
                response = await self._try_provider(provider, prompt)
                
                _LOGGER.info(
                    "[FallbackChain] SUCCESS: Provider '%s' generated response (attempt %d/%d)",
                    provider_name, attempt, total
                )
                
                return response
                
            except asyncio.TimeoutError as e:
                last_error = e
                _LOGGER.warning(
                    "[FallbackChain] TIMEOUT: Provider '%s' timed out after %ds (attempt %d/%d)",
                    provider_name, self.config.timeout_seconds, attempt, total
                )
                
            except Exception as e:
                last_error = e
                _LOGGER.warning(
                    "[FallbackChain] ERROR: Provider '%s' failed: %s (attempt %d/%d)",
                    provider_name, e, attempt, total
                )

        # All providers failed
        provider_names = ', '.join(p.name for p in self.providers)
        _LOGGER.error(
            "[FallbackChain] ALL PROVIDERS FAILED: Tried %d providers (%s). Last error: %s",
            len(self.providers), provider_names, last_error
        )
        
        if last_error:
            raise last_error
        else:
            raise Exception("All LLM providers failed")

    async def _try_provider(
        self, 
        provider: BaseLLMProvider, 
        prompt: str
    ) -> str:
        """
        Try to generate a response with a single provider.
        
        Args:
            provider: The provider instance to use
            prompt: The input prompt
            
        Returns:
            The generated response
            
        Raises:
            Exception: If generation fails
        """
        return await provider.generate(prompt)

    def get_available_providers(self) -> List[str]:
        """Return list of available provider names."""
        return [p.name for p in self.providers]

    def get_primary_provider(self) -> Optional[str]:
        """Return the name of the primary (first) provider."""
        return self.providers[0].name if self.providers else None


def create_fallback_chain_from_yaml(yaml_config: dict) -> LLMFallbackChain:
    """
    Create a FallbackChain from YAML configuration.
    
    Args:
        yaml_config: Dictionary from configuration.yaml
        
    Returns:
        Configured LLMFallbackChain instance
    """
    config = FallbackConfig(
        fallback_enabled=yaml_config.get("fallback_enabled", True),
        fallback_order=yaml_config.get("fallback_order", ["openai", "ollama", "ollama_tiny"]),
        provider=yaml_config.get("provider", "gpt-4"),
        openai_api_key=yaml_config.get("openai_api_key"),
        ollama_url=yaml_config.get("ollama_url", "http://localhost:11434"),
        ollama_model=yaml_config.get("ollama_model", "qwen3.5"),
        ollama_tiny_model=yaml_config.get("ollama_tiny_model", "qwen3.5:7b"),
        timeout_seconds=yaml_config.get("timeout_seconds", 30),
    )
    
    return LLMFallbackChain(config)
