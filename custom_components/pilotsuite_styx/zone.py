"""PilotSuite Styx Zone — HA-235.

Sync mit Core API: /api/v1/zones/*, /api/v1/areas/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup zone entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreZoneSensor(core_url, "Living Room", "living_room")]
    async_add_entities(entities)

class CoreZoneSensor(BinarySensorEntity):
    """Binary sensor for zone occupancy."""
    def __init__(self, core_url: str, name: str, zone_id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name} Zone"
        self._attr_unique_id = f"pilotsuite_zone_{zone_id}"
        self._attr_is_on = False
    
    def update(self):
        """Update zone state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/zones/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            occupied = data.get("occupied", [])
            self._attr_is_on = self._attr_unique_id in occupied
