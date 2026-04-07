"""PilotSuite Styx System Health — HA-282.

Sync mit Core API: /api/v1/health/system/*
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
    """Setup system health sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreSystemHealthSensor(core_url)]
    async_add_entities(entities)

class CoreSystemHealthSensor(SensorEntity):
    """Sensor for Core system health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite System Health"
        self._attr_unique_id = "pilotsuite_system_health"
        self._attr_native_value = "unknown"
    
    def update(self):
        """Update system health from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/health/system/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("status", "unknown")
