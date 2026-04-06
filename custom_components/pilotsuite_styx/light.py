"""PilotSuite Styx Light Entity — HA-222.

Sync mit Core API: /api/v1/lights/*, /api/v1/scenes/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup light entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreLightEntity(core_url)]
    async_add_entities(entities)

class CoreLightEntity(LightEntity):
    """Light entity for Core lighting control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Light"
        self._attr_unique_id = "pilotsuite_light"
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_is_on = False
        self._attr_brightness = 255
    
    def turn_on(self, **kwargs):
        """Turn light on."""
        brightness = kwargs.get("brightness", 255)
        requests.post(f"{self._core_url}/api/v1/lights/set", json={"brightness": int(brightness / 255 * 100)}, timeout=5)
        self._attr_is_on = True
        self._attr_brightness = brightness
    
    def turn_off(self, **kwargs):
        """Turn light off."""
        self._attr_is_on = False
    
    def update(self):
        """Update light state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/lights/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            lights = data.get("lights", [])
            if lights:
                self._attr_is_on = lights[0].get("on", False)
