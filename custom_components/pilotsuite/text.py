"""PilotSuite Styx Text Entities — HA-194.

Sync mit Core API: /api/v1/search/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup text entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreSearchQueryText(core_url)]
    async_add_entities(entities)

class CoreSearchQueryText(TextEntity):
    """Text entity for Core search queries."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Search Query"
        self._attr_unique_id = "pilotsuite_search_query"
        self._attr_native_value = ""
    
    def set_value(self, value: str) -> None:
        """Set search query and trigger search."""
        self._attr_native_value = value
        requests.get(f"{self._core_url}/api/v1/search/advanced?q={value}", timeout=5)
