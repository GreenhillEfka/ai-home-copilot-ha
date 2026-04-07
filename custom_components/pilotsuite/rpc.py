"""PilotSuite Styx RPC — HA-254.

Sync mit Core API: /api/v1/rpc/*
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
    """Setup RPC sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreRPCSensor(core_url)]
    async_add_entities(entities)

class CoreRPCSensor(SensorEntity):
    """Sensor for Core RPC endpoint."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite RPC"
        self._attr_unique_id = "pilotsuite_rpc"
        self._attr_native_value = "2.0"
    
    def update(self):
        """Update RPC version from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/rpc/version", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("version", "2.0")
