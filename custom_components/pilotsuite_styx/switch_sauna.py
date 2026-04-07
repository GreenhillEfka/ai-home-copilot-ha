"""PilotSuite Styx Sauna Switch — HA-216.

Sync mit Core API: /api/v1/sauna/*
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
    """Setup sauna switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreSaunaSwitch(core_url)]
    async_add_entities(entities)

class CoreSaunaSwitch(SwitchEntity):
    """Switch entity for sauna control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Sauna"
        self._attr_unique_id = "pilotsuite_sauna"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Turn sauna on."""
        self._attr_is_on = True
        requests.post(f"{self._core_url}/api/v1/sauna/on", timeout=5)
    
    def turn_off(self, **kwargs):
        """Turn sauna off."""
        self._attr_is_on = False
        requests.post(f"{self._core_url}/api/v1/sauna/off", timeout=5)
    
    def update(self):
        """Update sauna state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/sauna/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_is_on = data.get("on", False)
