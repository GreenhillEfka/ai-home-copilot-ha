"""PilotSuite Styx Camera Entity — HA-231.

Sync mit Core API: /api/v1/cameras/*
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
    """Setup camera entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreCameraEntity(core_url)]
    async_add_entities(entities)

class CoreCameraEntity(Camera):
    """Camera entity for Core stream."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Camera"
        self._attr_unique_id = "pilotsuite_camera"
        self._attr_is_recording = False
        self._attr_is_on = True
    
    def camera_image(self, width=None, height=None):
        """Get camera image."""
        resp = requests.get(f"{self._core_url}/api/v1/cameras/snapshot", timeout=5)
        if resp.status_code == 200:
            return resp.content
        return None
    
    def update(self):
        """Update camera state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/cameras/record", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_is_recording = data.get("recording", False)
