"""PilotSuite Styx Vacation Mode — HA-217.

Sync mit Core API: /api/v1/vacation/*
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
    """Setup vacation mode switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreVacationModeSwitch(core_url)]
    async_add_entities(entities)

class CoreVacationModeSwitch(SwitchEntity):
    """Switch entity for vacation mode."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Vacation Mode"
        self._attr_unique_id = "pilotsuite_vacation_mode"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Enable vacation mode."""
        self._attr_is_on = True
        requests.post(f"{self._core_url}/api/v1/vacation/on", timeout=5)
    
    def turn_off(self, **kwargs):
        """Disable vacation mode."""
        self._attr_is_on = False
        requests.post(f"{self._core_url}/api/v1/vacation/off", timeout=5)
    
    def update(self):
        """Update vacation mode state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/vacation/mode", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_is_on = data.get("active", False)
