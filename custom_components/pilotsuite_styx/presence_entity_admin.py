"""PilotSuite Styx Presence Entity Admin — HA-478.
Admin sensors for Presence Entity management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        PresenceEntityAdminSensor(core_url),
        PresenceActiveSensor(core_url),
        PresenceByTypeSensor(core_url)
    ])

class PresenceEntityAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Presence Entities"
        self._attr_unique_id = "pilotsuite_presence_entities_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/entities/presence", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class PresenceActiveSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Active Presence"
        self._attr_unique_id = "pilotsuite_active_presence"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/entities/presence/active", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class PresenceByTypeSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Presence Types"
        self._attr_unique_id = "pilotsuite_presence_types"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/entities/presence/summary", timeout=5)
        if resp.status_code == 200:
            types = resp.json().get("summary", {}).get("by_type", {})
            self._attr_native_value = len(types)
