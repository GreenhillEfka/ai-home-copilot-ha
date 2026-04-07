"""PilotSuite Styx Profile — HA-246.

Sync mit Core API: /api/v1/profiles/*, /api/v1/users/*
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
    """Setup profile select from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreProfileSelect(core_url)]
    async_add_entities(entities)

class CoreProfileSelect(SelectEntity):
    """Select entity for profile switching."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Profile"
        self._attr_unique_id = "pilotsuite_profile"
        self._attr_options = []
        self._attr_current_option = None
    
    def update(self):
        """Update profiles from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/profiles/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            profiles = data.get("profiles", [])
            self._attr_options = [p.get("name") for p in profiles]
    
    def select_option(self, option):
        """Switch profile."""
        requests.post(f"{self._core_url}/api/v1/users/switch", json={"user_id": option}, timeout=5)
        self._attr_current_option = option
