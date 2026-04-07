"""PilotSuite Styx Outage — HA-342.
Auto-Sync Core: /api/v1/outages/*
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
    async_add_entities([CoreOutageSensor(core_url)])
class CoreOutageSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Outages"
        self._attr_unique_id = "pilotsuite_outages"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/outages/active", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("active", 0)
