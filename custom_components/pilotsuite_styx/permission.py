"""PilotSuite Styx Permission — HA-247.

Sync mit Core API: /api/v1/roles/*, /api/v1/permissions/*
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
    """Setup permission switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CorePermissionSwitch(core_url)]
    async_add_entities(entities)

class CorePermissionSwitch(SwitchEntity):
    """Switch entity for permission control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Permission"
        self._attr_unique_id = "pilotsuite_permission"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Grant permission."""
        requests.post(f"{self._core_url}/api/v1/permissions/grant", json={"permission": "full", "user": "current"}, timeout=5)
        self._attr_is_on = True
    
    def turn_off(self, **kwargs):
        """Revoke permission."""
        self._attr_is_on = False
