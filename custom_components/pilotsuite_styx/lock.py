"""PilotSuite Styx Lock Entities — HA-206.

Sync mit Core API: /api/v1/lock/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup lock entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreLockEntity(core_url)]
    async_add_entities(entities)

class CoreLockEntity(LockEntity):
    """Lock entity for Core door lock."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Door Lock"
        self._attr_unique_id = "pilotsuite_door_lock"
        self._attr_is_locked = True
    
    def lock(self, **kwargs):
        """Lock the door."""
        self._attr_is_locked = True
        requests.post(f"{self._core_url}/api/v1/lock/set", json={"state": "locked"}, timeout=5)
    
    def unlock(self, **kwargs):
        """Unlock the door."""
        self._attr_is_locked = False
        requests.post(f"{self._core_url}/api/v1/lock/set", json={"state": "unlocked"}, timeout=5)
