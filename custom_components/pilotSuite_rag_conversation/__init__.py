"""
PilotSuite RAG Conversation für HomeAssistant

Nutzt RAG-API für kontextuelle Antworten mit:
- HA-States
- Dokumenten
- History
- Optional: Web-Suche (SearXNG)

Architektur: LLM-Fallback-Chain mit RAG-Kontext-Injektion.
"""

import asyncio
import logging
from typing import Optional

import aiohttp
try:
    import async_timeout
except ImportError:
    import asyncio as async_timeout
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_MODEL,
    CONF_RAG_API_URL,
    CONF_USE_WEB_SEARCH,
    DEFAULT_MODEL,
    DEFAULT_RAG_API_URL,
    DEFAULT_USE_WEB_SEARCH,
    DOMAIN,
)
from .llm_fallback import LLMFallbackChain, FallbackConfig
from .conversation import PilotSuiteRAGConversationHandler

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PilotSuite RAG Conversation component from YAML."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    
    # LLM-Fallback-Chain initialisieren mit Config
    fallback_config = FallbackConfig(
        fallback_enabled=conf.get("fallback_enabled", True),
        fallback_order=conf.get("fallback_order", ["openai", "ollama", "ollama_tiny"]),
        provider=conf.get(CONF_MODEL, DEFAULT_MODEL),
        openai_api_key=conf.get(CONF_API_KEY),
        ollama_url=conf.get("ollama_url", "http://localhost:11434"),
        ollama_model=conf.get("ollama_model", "qwen3.5"),
        ollama_tiny_model=conf.get("ollama_tiny_model", "qwen3.5:7b"),
        timeout_seconds=conf.get("timeout_seconds", 30),
    )
    
    fallback_chain = LLMFallbackChain(fallback_config)
    
    hass.data[DOMAIN] = {
        CONF_RAG_API_URL: conf.get(CONF_RAG_API_URL, DEFAULT_RAG_API_URL),
        CONF_USE_WEB_SEARCH: conf.get(CONF_USE_WEB_SEARCH, DEFAULT_USE_WEB_SEARCH),
        "fallback_chain": fallback_chain,
    }

    # Conversation Handler initialisieren
    handler = PilotSuiteRAGConversationHandler(
        hass,
        fallback_chain=fallback_chain,
        rag_api_url=hass.data[DOMAIN][CONF_RAG_API_URL],
        use_web_search=hass.data[DOMAIN][CONF_USE_WEB_SEARCH],
    )
    await handler.async_init()

    # Register conversation agent
    conversation.async_set_agent(hass, config, handler)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PilotSuite RAG Conversation from a config entry."""
    rag_api_url = entry.data.get(CONF_RAG_API_URL, DEFAULT_RAG_API_URL)
    openai_api_key = entry.data.get(CONF_API_KEY)
    model = entry.options.get(CONF_MODEL, DEFAULT_MODEL)
    use_web_search = entry.options.get(CONF_USE_WEB_SEARCH, DEFAULT_USE_WEB_SEARCH)

    # LLM-Fallback-Chain initialisieren mit Config Entry
    fallback_config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        provider=model,
        openai_api_key=openai_api_key,
        ollama_url="http://localhost:11434",
        ollama_model="qwen3.5",
        ollama_tiny_model="qwen3.5:7b",
        timeout_seconds=30,
    )
    
    fallback_chain = LLMFallbackChain(fallback_config)

    handler = PilotSuiteRAGConversationHandler(
        hass,
        fallback_chain=fallback_chain,
        rag_api_url=rag_api_url,
        use_web_search=use_web_search,
    )
    await handler.async_init()

    conversation.async_set_agent(hass, entry, handler)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cleanup handler resources
    agent = conversation.async_get_agent(hass, entry)
    if agent and hasattr(agent, 'async_cleanup'):
        await agent.async_cleanup()
    
    conversation.async_unset_agent(hass, entry)
    return True
