"""PilotSuite Styx Select Entities — HA-195.

Sync mit Core API: /api/v1/tags/*, /api/v1/options/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup select entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreTagSelect(core_url)]
    async_add_entities(entities)

class CoreTagSelect(SelectEntity):
    """Select entity for Core tag selection."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Tag Selection"
        self._attr_unique_id = "pilotsuite_tag_select"
        self._attr_options = ["tag1", "tag2", "tag3"]
        self._attr_current_option = None
    
    def select_option(self, option: str) -> None:
        """Select a tag and sync with Core."""
        self._attr_current_option = option
        requests.post(f"{self._core_url}/api/v1/tags/create", json={"name": option}, timeout=5)
