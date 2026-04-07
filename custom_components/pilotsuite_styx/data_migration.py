"""PilotSuite Styx Data Migration — HA-293.

Sync mit Core API: /api/v1/migration/*
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
    """Setup data migration sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreDataMigrationSensor(core_url)]
    async_add_entities(entities)

class CoreDataMigrationSensor(SensorEntity):
    """Sensor for Core data migration status."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Data Migration"
        self._attr_unique_id = "pilotsuite_data_migration"
        self._attr_native_value = "idle"
    
    def update(self):
        """Update data migration status from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/migration/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("status", "idle")
