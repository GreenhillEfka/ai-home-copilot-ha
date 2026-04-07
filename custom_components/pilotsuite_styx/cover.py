"""PilotSuite Styx Cover Entity — HA-223.

Sync mit Core API: /api/v1/covers/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup cover entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreCoverEntity(core_url)]
    async_add_entities(entities)

class CoreCoverEntity(CoverEntity):
    """Cover entity for Core blinds control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Cover"
        self._attr_unique_id = "pilotsuite_cover"
        self._attr_supported_features = (
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.SET_POSITION
        )
        self._attr_current_cover_position = 100
    
    def open_cover(self, **kwargs):
        """Open the cover."""
        requests.post(f"{self._core_url}/api/v1/covers/open", timeout=5)
        self._attr_current_cover_position = 100
    
    def close_cover(self, **kwargs):
        """Close the cover."""
        requests.post(f"{self._core_url}/api/v1/covers/close", timeout=5)
        self._attr_current_cover_position = 0
    
    def set_cover_position(self, position, **kwargs):
        """Set cover position."""
        requests.post(f"{self._core_url}/api/v1/covers/set", json={"position": position}, timeout=5)
        self._attr_current_cover_position = position
    
    def update(self):
        """Update cover state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/covers/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            covers = data.get("covers", [])
            if covers:
                self._attr_current_cover_position = covers[0].get("position", 100)
