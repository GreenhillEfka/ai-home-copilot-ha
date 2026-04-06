"""PilotSuite Styx Climate Entity — HA-221.

Sync mit Core API: /api/v1/climate/*, /api/v1/hvac/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup climate entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreClimateEntity(core_url)]
    async_add_entities(entities)

class CoreClimateEntity(ClimateEntity):
    """Climate entity for Core HVAC control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Climate"
        self._attr_unique_id = "pilotsuite_climate"
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = 22.0
    
    def set_temperature(self, **kwargs):
        """Set target temperature."""
        temp = kwargs.get("temperature")
        requests.post(f"{self._core_url}/api/v1/climate/set", json={"temp": temp}, timeout=5)
        self._attr_target_temperature = temp
    
    def set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        requests.post(f"{self._core_url}/api/v1/hvac/mode", json={"mode": hvac_mode}, timeout=5)
        self._attr_hvac_mode = hvac_mode
    
    def turn_on(self):
        """Turn climate on."""
        self.set_hvac_mode(HVACMode.HEAT)
    
    def turn_off(self):
        """Turn climate off."""
        self.set_hvac_mode(HVACMode.OFF)
    
    def update(self):
        """Update climate state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/climate/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_target_temperature = data.get("temp", 22.0)
