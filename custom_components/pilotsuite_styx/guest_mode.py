"""PilotSuite Styx Guest Mode — HA-218.

Sync mit Core API: /api/v1/guest/*, /api/v1/access/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup guest mode switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreGuestModeSwitch(core_url)]
    async_add_entities(entities)

class CoreGuestModeSwitch(SwitchEntity):
    """Switch entity for guest mode."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Guest Mode"
        self._attr_unique_id = "pilotsuite_guest_mode"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Enable guest mode."""
        self._attr_is_on = True
        requests.post(f"{self._core_url}/api/v1/guest/add", json={"name": "guest"}, timeout=5)
    
    def turn_off(self, **kwargs):
        """Disable guest mode."""
        self._attr_is_on = False
        requests.post(f"{self._core_url}/api/v1/guest/remove", json={"name": "guest"}, timeout=5)
