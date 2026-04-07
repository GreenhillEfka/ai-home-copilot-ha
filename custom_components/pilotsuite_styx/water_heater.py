"""PilotSuite Styx Water Heater Entities — HA-200.

Sync mit Core API: /api/v1/integrations/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup water heater entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreIntegrationWaterHeater(core_url)]
    async_add_entities(entities)

class CoreIntegrationWaterHeater(WaterHeaterEntity):
    """Water heater entity for Core integration status."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Integration Status"
        self._attr_unique_id = "pilotsuite_integration_status"
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
        self._attr_temperature_unit = "°C"
        self._attr_current_temperature = 45.0
        self._attr_target_temperature = 50.0
    
    def set_temperature(self, **kwargs):
        """Set temperature and sync with Core integration."""
        self._attr_target_temperature = kwargs.get("temperature")
        requests.post(f"{self._core_url}/api/v1/integrations/register", json={
            "id": "water_heater",
            "target_temp": self._attr_target_temperature
        }, timeout=5)
