"""PilotSuite Styx Room Context — HA-467.
Auto-Sync Core: /api/v1/contexts/rooms/*
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([RoomContextSensor(core_url)])

class RoomContextSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Room Contexts"
        self._attr_unique_id = "pilotsuite_room_contexts"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/contexts/rooms", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = len(resp.json().get("contexts", []))
