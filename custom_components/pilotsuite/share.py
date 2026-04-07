"""PilotSuite Styx Share — HA-456.
Auto-Sync Core: /api/v1/shares/*
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)
async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([CoreShareSensor(core_url)])
class CoreShareSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Shares"
        self._attr_unique_id = "pilotsuite_shares"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/shares/list", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = len(resp.json().get("shares", []))
