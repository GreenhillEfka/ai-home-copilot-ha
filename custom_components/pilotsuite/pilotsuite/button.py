"""PilotSuite Styx Buttons — HA-191.

Sync mit Core API: /api/v1/data/*, /api/v1/backup/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup buttons from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreExportButton(core_url),
        CoreImportButton(core_url),
        CoreBackupNowButton(core_url),
    ]
    async_add_entities(entities)

class CoreExportButton(ButtonEntity):
    """Button to trigger data export."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Export Core Data"
        self._attr_unique_id = "pilotsuite_data_export"
    
    def press(self):
        requests.get(f"{self._core_url}/api/v1/data/export", timeout=10)

class CoreImportButton(ButtonEntity):
    """Button to trigger data import."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Import Core Data"
        self._attr_unique_id = "pilotsuite_data_import"
    
    def press(self):
        requests.post(f"{self._core_url}/api/v1/data/import", json={}, timeout=10)

class CoreBackupNowButton(ButtonEntity):
    """Button to trigger immediate backup."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Create Backup Now"
        self._attr_unique_id = "pilotsuite_backup_now"
    
    def press(self):
        requests.post(f"{self._core_url}/api/v1/backup/create", json={"name": "manual"}, timeout=10)
