"""PilotSuite Styx Maintenance — HA-346.
Auto-Sync Core: /api/v1/maintenance/*
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
    async_add_entities([CoreMaintenanceSensor(core_url)])
class CoreMaintenanceSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Maintenance"
        self._attr_unique_id = "pilotsuite_maintenance"
        self._attr_native_value = "none"
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/maintenance/status", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("status", "none")
