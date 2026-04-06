"""PilotSuite Styx Room Context Admin — HA-476.
Admin sensors for Room Context management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        RoomContextAdminSensor(core_url),
        RoomContextActiveSensor(core_url),
        RoomContextLearnedSensor(core_url)
    ])

class RoomContextAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Room Contexts"
        self._attr_unique_id = "pilotsuite_room_contexts_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/contexts/rooms", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class RoomContextActiveSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Active Contexts"
        self._attr_unique_id = "pilotsuite_active_contexts"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/contexts/rooms/active", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class RoomContextLearnedSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Learned Contexts"
        self._attr_unique_id = "pilotsuite_learned_contexts"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/contexts/rooms/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("learned_contexts", 0)
