"""Config flow for PilotSuite RAG Conversation.

Einfacher Flow für HA Token + optionaler OpenAI-Key.
"""

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MODEL,
    CONF_RAG_API_URL,
    CONF_USE_WEB_SEARCH,
    DEFAULT_MODEL,
    DEFAULT_RAG_API_URL,
    DEFAULT_USE_WEB_SEARCH,
    DOMAIN,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)


class PilotSuiteRAGConversationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PilotSuite RAG Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.
        
        Config Flow für:
        - HA Token (erforderlich für RAG-API)
        - OpenAI-Key (optional, für Fallback-Chain)
        """
        errors = {}

        if user_input is not None:
            # Validate RAG-API URL
            rag_api_url = user_input[CONF_RAG_API_URL]
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{rag_api_url}/health",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        if resp.status != 200:
                            errors["base"] = "rag_api_unreachable"
            except aiohttp.ClientError:
                errors["base"] = "rag_api_unreachable"
            except Exception:
                errors["base"] = "rag_api_unreachable"

            if not errors:
                # HA Token (für RAG-API) + optionaler OpenAI-Key
                return self.async_create_entry(
                    title="PilotSuite RAG Conversation",
                    data={
                        CONF_RAG_API_URL: rag_api_url,
                        CONF_API_KEY: user_input.get(CONF_API_KEY, ""),  # Optional für Fallback
                    },
                    options={
                        CONF_MODEL: user_input.get(CONF_MODEL, DEFAULT_MODEL),
                        CONF_USE_WEB_SEARCH: user_input.get(
                            CONF_USE_WEB_SEARCH, DEFAULT_USE_WEB_SEARCH
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RAG_API_URL,
                        default=DEFAULT_RAG_API_URL,
                    ): str,
                    vol.Optional(CONF_API_KEY, default=""): str,  # Optional: OpenAI-Key für Fallback
                    vol.Required(
                        CONF_MODEL,
                        default=DEFAULT_MODEL,
                    ): vol.In(SUPPORTED_MODELS),
                    vol.Required(
                        CONF_USE_WEB_SEARCH,
                        default=DEFAULT_USE_WEB_SEARCH,
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options step."""
        if user_input is not None:
            return self.async_create_entry(
                title="PilotSuite RAG Conversation",
                data=self._async_current_entry().data,
                options=user_input,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODEL,
                        default=self._async_current_entry().options.get(
                            CONF_MODEL, DEFAULT_MODEL
                        ),
                    ): vol.In(SUPPORTED_MODELS),
                    vol.Required(
                        CONF_USE_WEB_SEARCH,
                        default=self._async_current_entry().options.get(
                            CONF_USE_WEB_SEARCH, DEFAULT_USE_WEB_SEARCH
                        ),
                    ): bool,
                }
            ),
        )
