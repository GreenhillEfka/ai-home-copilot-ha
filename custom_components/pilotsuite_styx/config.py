"""PilotSuite Styx Config — HA-245.

Sync mit Core API: /api/v1/config/*, /api/v1/settings/*
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
    """Setup config switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreConfigSwitch(core_url)]
    async_add_entities(entities)

class CoreConfigSwitch(SwitchEntity):
    """Switch entity for config sync."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Config Sync"
        self._attr_unique_id = "pilotsuite_config_sync"
        self._attr_is_on = True
    
    def turn_on(self, **kwargs):
        """Enable config sync."""
        requests.post(f"{self._core_url}/api/v1/config/set", json={"key": "sync", "value": True}, timeout=5)
        self._attr_is_on = True
    
    def turn_off(self, **kwargs):
        """Disable config sync."""
        self._attr_is_on = False
