"""PilotSuite Styx Cover Entities — HA-205.

Sync mit Core API: /api/v1/cover/*
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
    """Setup cover entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreCoverEntity(core_url)]
    async_add_entities(entities)

class CoreCoverEntity(CoverEntity):
    """Cover entity for Core blinds/curtains."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Cover"
        self._attr_unique_id = "pilotsuite_cover"
        self._attr_supported_features = CoverEntityFeature.SET_POSITION | CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
        self._attr_current_cover_position = 0
        self._attr_is_closed = True
    
    def open_cover(self, **kwargs):
        """Open cover."""
        self._attr_is_closed = False
        self._attr_current_cover_position = 100
        requests.post(f"{self._core_url}/api/v1/cover/set", json={"state": "open"}, timeout=5)
    
    def close_cover(self, **kwargs):
        """Close cover."""
        self._attr_is_closed = True
        self._attr_current_cover_position = 0
        requests.post(f"{self._core_url}/api/v1/cover/set", json={"state": "close"}, timeout=5)
    
    def set_cover_position(self, position: int) -> None:
        """Set cover position."""
        self._attr_current_cover_position = position
        self._attr_is_closed = position == 0
        requests.post(f"{self._core_url}/api/v1/cover/set", json={"position": position}, timeout=5)
