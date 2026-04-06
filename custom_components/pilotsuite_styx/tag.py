"""PilotSuite Styx Tag — HA-236.

Sync mit Core API: /api/v1/tags/*, /api/v1/labels/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.select import SelectEntity
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup tag select from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreTagSelect(core_url)]
    async_add_entities(entities)

class CoreTagSelect(SelectEntity):
    """Select entity for tag assignment."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Tags"
        self._attr_unique_id = "pilotsuite_tags"
        self._attr_options = []
        self._attr_current_option = None
    
    def update(self):
        """Update tags from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/tags/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            tags = data.get("tags", [])
            self._attr_options = [t.get("name") for t in tags]
    
    def select_option(self, option):
        """Assign tag."""
        requests.post(f"{self._core_url}/api/v1/labels/assign", json={"label_id": option}, timeout=5)
        self._attr_current_option = option
