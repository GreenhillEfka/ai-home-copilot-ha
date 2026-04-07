"""PilotSuite Styx Logging — HA-263.

Sync mit Core API: /api/v1/logs/*
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
    """Setup logging sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreLoggingSensor(core_url)]
    async_add_entities(entities)

class CoreLoggingSensor(SensorEntity):
    """Sensor for Core log level."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Log Level"
        self._attr_unique_id = "pilotsuite_logging"
        self._attr_native_value = "info"
    
    def update(self):
        """Update log level from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/logs/levels", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            levels = data.get("levels", [])
            if levels:
                self._attr_native_value = levels[0]
