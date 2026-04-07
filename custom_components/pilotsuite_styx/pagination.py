"""PilotSuite Styx Pagination — HA-319.
Auto-Sync Core: /api/v1/pagination/*
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
    async_add_entities([CorePaginationSensor(core_url)])
class CorePaginationSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Page Size"
        self._attr_unique_id = "pilotsuite_pagination"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/pagination/config", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("page_size", 0)
