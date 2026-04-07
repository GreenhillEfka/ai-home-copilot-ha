"""PilotSuite Styx Schema Version — HA-292.

Sync mit Core API: /api/v1/schema/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup schema version sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreSchemaVersionSensor(core_url)]
    async_add_entities(entities)

class CoreSchemaVersionSensor(SensorEntity):
    """Sensor for Core schema version."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Schema Version"
        self._attr_unique_id = "pilotsuite_schema_version"
        self._attr_native_value = "unknown"
    
    def update(self):
        """Update schema version from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/schema/version", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("version", "unknown")
