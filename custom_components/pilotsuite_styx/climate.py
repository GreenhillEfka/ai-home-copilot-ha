"""PilotSuite Styx Climate Entities — HA-203.

Sync mit Core API: /api/v1/climate/*
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
    """Setup climate entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreClimateEntity(core_url)]
    async_add_entities(entities)

class CoreClimateEntity(ClimateEntity):
    """Climate entity for Core HVAC."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Climate"
        self._attr_unique_id = "pilotsuite_climate"
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_target_temperature = 21.5
        self._attr_current_temperature = 20.0
        self._attr_temperature_unit = "°C"
    
    def set_temperature(self, **kwargs):
        """Set target temperature."""
        self._attr_target_temperature = kwargs.get("temperature")
        requests.post(f"{self._core_url}/api/v1/climate/set", json={"temperature": self._attr_target_temperature}, timeout=5)
    
    def set_hvac_mode(self, hvac_mode: str) -> None:
        """Set HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        requests.post(f"{self._core_url}/api/v1/climate/set", json={"hvac_mode": hvac_mode}, timeout=5)
