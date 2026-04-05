"""PilotSuite Styx Camera Entities — HA-202.

Sync mit Core API: /api/v1/camera/*, /api/v1/media/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup camera entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreStreamCamera(core_url)]
    async_add_entities(entities)

class CoreStreamCamera(Camera):
    """Camera entity for Core stream."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Stream"
        self._attr_unique_id = "pilotsuite_core_stream"
        self._stream_url = None
    
    def camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Return camera image."""
        resp = requests.get(f"{self._core_url}/api/v1/camera/stream", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._stream_url = data.get("stream_url")
        return None
    
    @property
    def stream_source(self) -> str | None:
        """Return the source of the stream."""
        return self._stream_url
