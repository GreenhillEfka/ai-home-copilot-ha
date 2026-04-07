"""PilotSuite Styx Search — HA-257.

Sync mit Core API: /api/v1/search/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup search sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreSearchSensor(core_url)]
    async_add_entities(entities)

class CoreSearchSensor(SensorEntity):
    """Sensor for Core search index size."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Search Index"
        self._attr_unique_id = "pilotsuite_search"
        self._attr_native_value = 0
    
    def update(self):
        """Update search index from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/search/suggest", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = len(data.get("suggestions", []))
