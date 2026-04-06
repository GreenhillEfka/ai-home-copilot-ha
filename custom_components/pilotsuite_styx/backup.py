"""PilotSuite Styx Backup — HA-239.

Sync mit Core API: /api/v1/backups/*
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
    """Setup backup buttons from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreBackupButton(core_url, "Create Backup", "create"),
        CoreBackupButton(core_url, "Restore Backup", "restore"),
    ]
    async_add_entities(entities)

class CoreBackupButton(ButtonEntity):
    """Button entity for backup operations."""
    def __init__(self, core_url: str, name: str, action: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_backup_{action}"
        self._action = action
    
    def press(self, **kwargs):
        """Execute backup action."""
        if self._action == "create":
            requests.post(f"{self._core_url}/api/v1/backups/create", json={"name": "manual_backup"}, timeout=5)
        elif self._action == "restore":
            requests.post(f"{self._core_url}/api/v1/backups/restore", json={"backup_id": "latest"}, timeout=5)
