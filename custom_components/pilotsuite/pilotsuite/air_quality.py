"""PilotSuite Styx Air Quality Entities — HA-208.

Sync mit Core API: /api/v1/air_quality/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.air_quality import AirQualityEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup air quality entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreAirQualityEntity(core_url)]
    async_add_entities(entities)

class CoreAirQualityEntity(AirQualityEntity):
    """Air quality entity for Core monitoring."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Air Quality"
        self._attr_unique_id = "pilotsuite_air_quality"
        self._attr_pm_2_5 = 10
        self._attr_pm_10 = 20
        self._attr_nitrogen_dioxide = 15
        self._attr_ozon = 30
        self._attr_carbon_monoxide = 5
        self._attr_volatile_organic_compounds = 100
    
    def update(self):
        """Update air quality data from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/air_quality/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_pm_2_5 = data.get("pm25", 10)
            self._attr_pm_10 = data.get("pm10", 20)
