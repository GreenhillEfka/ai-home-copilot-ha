"""PilotSuite Styx Debug — HA-421.
Auto-Sync Core: /api/v1/debug/*
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
    async_add_entities([CoreDebugSensor(core_url)])
class CoreDebugSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Debug"
        self._attr_unique_id = "pilotsuite_debug"
        self._attr_native_value = "disabled"
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/debug/info", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = "enabled" if resp.json().get("info", {}).get("enabled") else "disabled"
