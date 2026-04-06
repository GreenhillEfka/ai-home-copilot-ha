"""PilotSuite Styx Update Entity — HA-230.

Sync mit Core API: /api/v1/updates/*, /api/v1/firmware/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup update entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreUpdateEntity(core_url)]
    async_add_entities(entities)

class CoreUpdateEntity(UpdateEntity):
    """Update entity for Core firmware."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Firmware"
        self._attr_unique_id = "pilotsuite_firmware"
        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_installed_version = "1.0.0"
        self._attr_latest_version = "1.0.0"
        self._attr_update_available = False
    
    def install(self, **kwargs):
        """Install update."""
        requests.post(f"{self._core_url}/api/v1/updates/install", json={"update_id": self._attr_latest_version}, timeout=5)
    
    def update(self):
        """Update state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/firmware/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_installed_version = data.get("version", "1.0.0")
            self._attr_latest_version = data.get("latest", "1.0.0")
            self._attr_update_available = data.get("version") != data.get("latest")
