"""PilotSuite Styx Media Player — HA-220.

Sync mit Core API: /api/v1/media/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup media player from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreMediaPlayer(core_url)]
    async_add_entities(entities)

class CoreMediaPlayer(MediaPlayerEntity):
    """Media player entity for Core entertainment."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Media Player"
        self._attr_unique_id = "pilotsuite_media_player"
        self._attr_supported_features = (
            MediaPlayerEntityFeature.PLAY |
            MediaPlayerEntityFeature.PAUSE |
            MediaPlayerEntityFeature.VOLUME_SET
        )
        self._attr_state = "idle"
        self._attr_volume_level = 0.5
    
    def media_play(self):
        """Start playback."""
        requests.post(f"{self._core_url}/api/v1/media/play", timeout=5)
        self._attr_state = "playing"
    
    def media_pause(self):
        """Pause playback."""
        requests.post(f"{self._core_url}/api/v1/media/pause", timeout=5)
        self._attr_state = "paused"
    
    def set_volume_level(self, volume):
        """Set volume level."""
        requests.post(f"{self._core_url}/api/v1/media/volume", json={"level": int(volume * 100)}, timeout=5)
        self._attr_volume_level = volume
    
    def update(self):
        """Update media player state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/media/player", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_volume_level = data.get("volume", 50) / 100
