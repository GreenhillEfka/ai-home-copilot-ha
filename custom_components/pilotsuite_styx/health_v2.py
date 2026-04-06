"""PilotSuite Styx Health V2 — HA-418.
Auto-Sync Core: /api/v1/health/v2/*
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)
async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([CoreHealthV2Sensor(core_url)])
class CoreHealthV2Sensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Health V2"
        self._attr_unique_id = "pilotsuite_health_v2"
        self._attr_native_value = "unknown"
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/health/v2/full", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = "healthy" if resp.json().get("ok") else "unhealthy"
