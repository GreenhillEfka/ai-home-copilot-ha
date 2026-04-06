"""PilotSuite Styx Favorite — HA-306.
Auto-Sync Core: /api/v1/favorites/*
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
    async_add_entities([CoreFavoriteSensor(core_url)])
class CoreFavoriteSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Favorites"
        self._attr_unique_id = "pilotsuite_favorites"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/favorites/list", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = len(resp.json().get("favorites", []))
