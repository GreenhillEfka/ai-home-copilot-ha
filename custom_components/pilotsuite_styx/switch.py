"""PilotSuite Styx Switches — HA-190.

Sync mit Core API: /api/v1/auth/*, /api/v1/modules/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup switches from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreModuleReloadSwitch(core_url),
        CoreBackupSwitch(core_url),
    ]
    async_add_entities(entities)

class CoreModuleReloadSwitch(SwitchEntity):
    """Switch to reload Core modules."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Reload Core Modules"
        self._attr_unique_id = "pilotsuite_modules_reload"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        requests.post(f"{self._core_url}/api/v1/modules/reload", timeout=5)
        self._attr_is_on = False

class CoreBackupSwitch(SwitchEntity):
    """Switch to trigger Core backup."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Create Core Backup"
        self._attr_unique_id = "pilotsuite_backup_create"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        requests.post(f"{self._core_url}/api/v1/backup/create", json={"name": "ha_triggered"}, timeout=5)
        self._attr_is_on = False
