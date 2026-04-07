"""PilotSuite Styx Presence V3 — HA-458.
Auto-Sync Core: /api/v1/presence/v3/*
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)
async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([CorePresenceV3Sensor(core_url)])
class CorePresenceV3Sensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Presence V3"
        self._attr_unique_id = "pilotsuite_presence_v3"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/presence/v3/status", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("online", 0)
