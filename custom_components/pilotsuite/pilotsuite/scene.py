"""PilotSuite Styx Scene Entities — HA-198.

Sync mit Core API: /api/v1/services/*, /api/v1/scenes/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup scene entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        PilotSuiteScene(core_url, "scene_home", "Home Scene"),
        PilotSuiteScene(core_url, "scene_away", "Away Scene"),
        PilotSuiteScene(core_url, "scene_night", "Night Scene"),
    ]
    async_add_entities(entities)

class PilotSuiteScene(Scene):
    """Scene entity for PilotSuite."""
    def __init__(self, core_url: str, scene_id: str, scene_name: str):
        self._core_url = core_url
        self._scene_id = scene_id
        self._attr_name = f"PilotSuite {scene_name}"
        self._attr_unique_id = f"pilotsuite_{scene_id}"
    
    def activate(self, **kwargs):
        """Activate scene via Core API."""
        requests.post(f"{self._core_url}/api/v1/services/execute", json={
            "service": "scene.activate",
            "scene_id": self._scene_id
        }, timeout=5)
