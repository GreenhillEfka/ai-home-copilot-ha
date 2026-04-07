"""PilotSuite Styx Weather Entity — HA-210.

Sync mit Core API: /api/v1/weather/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup weather entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreWeatherEntity(core_url)]
    async_add_entities(entities)

class CoreWeatherEntity(WeatherEntity):
    """Weather entity for Core forecast."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Weather"
        self._attr_unique_id = "pilotsuite_weather"
        self._attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
        self._attr_temperature = 20.0
        self._attr_humidity = 65
        self._attr_pressure = 1013
        self._attr_wind_speed = 10.0
        self._attr_condition = "sunny"
    
    def update(self):
        """Update weather data from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/weather/forecast", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            forecast = data.get("forecast", [])
            if forecast:
                self._attr_temperature = forecast[0].get("temp", 20.0)
                self._attr_condition = forecast[0].get("condition", "sunny")
    
    @property
    def forecast(self):
        """Return forecast."""
        resp = requests.get(f"{self._core_url}/api/v1/weather/forecast", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("forecast", [])
        return []
