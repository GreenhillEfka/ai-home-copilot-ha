"""PilotSuite Styx Debug Log — HA-272.

Sync mit Core API: /api/v1/debug/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup debug sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreDebugSensor(core_url)]
    async_add_entities(entities)

class CoreDebugSensor(SensorEntity):
    """Sensor for Core debug log count."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Debug Logs"
        self._attr_unique_id = "pilotsuite_debug"
        self._attr_native_value = 0
    
    def update(self):
        """Update debug log count from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/debug/summary", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("total", 0)
