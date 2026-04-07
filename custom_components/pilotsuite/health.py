"""PilotSuite Styx Health — HA-261.

Sync mit Core API: /api/v1/health/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup health sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreHealthSensor(core_url)]
    async_add_entities(entities)

class CoreHealthSensor(BinarySensorEntity):
    """Binary sensor for Core health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Health"
        self._attr_unique_id = "pilotsuite_health"
        self._attr_is_on = True
    
    def update(self):
        """Update health from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/health/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_is_on = data.get("status") == "healthy"
        else:
            self._attr_is_on = False
