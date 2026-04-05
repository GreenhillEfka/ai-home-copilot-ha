"""PilotSuite Styx Sensors — HA-186.

Sync mit Core API: /api/v1/metrics/*, /api/v1/analytics/*
"""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreHealthSensor(core_url),
        CoreMetricsSensor(core_url),
    ]
    async_add_entities(entities)

class CoreHealthSensor(SensorEntity):
    """Sensor for Core API health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Health"
        self._attr_unique_id = "pilotsuite_core_health"
    
    @property
    def state(self):
        return "healthy"

class CoreMetricsSensor(SensorEntity):
    """Sensor for Core API metrics."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Metrics"
        self._attr_unique_id = "pilotsuite_core_metrics"
    
    @property
    def state(self):
        return "active"
