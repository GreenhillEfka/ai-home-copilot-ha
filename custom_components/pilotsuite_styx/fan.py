"""PilotSuite Styx Fan Entities — HA-204.

Sync mit Core API: /api/v1/fan/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup fan entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreFanEntity(core_url)]
    async_add_entities(entities)

class CoreFanEntity(FanEntity):
    """Fan entity for Core control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Fan"
        self._attr_unique_id = "pilotsuite_fan"
        self._attr_supported_features = FanEntityFeature.SET_SPEED
        self._attr_percentage_step = 1
        self._attr_percentage = 0
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Turn fan on."""
        self._attr_is_on = True
        requests.post(f"{self._core_url}/api/v1/fan/set", json={"state": "on"}, timeout=5)
    
    def turn_off(self, **kwargs):
        """Turn fan off."""
        self._attr_is_on = False
        requests.post(f"{self._core_url}/api/v1/fan/set", json={"state": "off"}, timeout=5)
    
    def set_percentage(self, percentage: int) -> None:
        """Set fan speed."""
        self._attr_percentage = percentage
        requests.post(f"{self._core_url}/api/v1/fan/set", json={"speed": percentage}, timeout=5)
