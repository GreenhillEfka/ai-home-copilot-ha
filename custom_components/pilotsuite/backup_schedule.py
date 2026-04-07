"""PilotSuite Styx Backup Schedule — HA-280.

Sync mit Core API: /api/v1/backup/schedule/*
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
    """Setup backup schedule sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreBackupScheduleSensor(core_url)]
    async_add_entities(entities)

class CoreBackupScheduleSensor(SensorEntity):
    """Sensor for Core backup schedule status."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Backup Schedule"
        self._attr_unique_id = "pilotsuite_backup_schedule"
        self._attr_native_value = "unknown"
    
    def update(self):
        """Update backup schedule status from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/backup/schedule/status", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("status", "unknown")
