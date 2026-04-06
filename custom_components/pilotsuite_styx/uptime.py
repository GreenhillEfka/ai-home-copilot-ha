"""PilotSuite Styx Uptime — HA-344.
Auto-Sync Core: /api/v1/uptime/*
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
    async_add_entities([CoreUptimeSensor(core_url)])
class CoreUptimeSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Uptime"
        self._attr_unique_id = "pilotsuite_uptime"
        self._attr_native_value = 0
        self._attr_native_unit_of_measurement = "%"
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/uptime/current", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("uptime_percent", 0)
