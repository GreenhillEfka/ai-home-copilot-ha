"""PilotSuite Styx Intent Manager Admin — HA-479.
Admin sensors for Intent Manager management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        IntentManagerAdminSensor(core_url),
        IntentActiveSensor(core_url),
        IntentWithScriptSensor(core_url)
    ])

class IntentManagerAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Intents"
        self._attr_unique_id = "pilotsuite_intents_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/intents", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class IntentActiveSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Active Intents"
        self._attr_unique_id = "pilotsuite_active_intents"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/intents/active", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class IntentWithScriptSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Linked Scripts"
        self._attr_unique_id = "pilotsuite_linked_scripts"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/intents/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("intents_with_script", 0)
