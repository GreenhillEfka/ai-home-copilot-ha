"""PilotSuite Styx Lock Entity — HA-224.

Sync mit Core API: /api/v1/locks/*
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
    """Setup lock entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreLockEntity(core_url)]
    async_add_entities(entities)

class CoreLockEntity(LockEntity):
    """Lock entity for Core door control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Lock"
        self._attr_unique_id = "pilotsuite_lock"
        self._attr_is_locked = False
    
    def lock(self, **kwargs):
        """Lock the door."""
        requests.post(f"{self._core_url}/api/v1/locks/lock", timeout=5)
        self._attr_is_locked = True
    
    def unlock(self, **kwargs):
        """Unlock the door."""
        requests.post(f"{self._core_url}/api/v1/locks/unlock", timeout=5)
        self._attr_is_locked = False
    
    def update(self):
        """Update lock state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/locks/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            locks = data.get("locks", [])
            if locks:
                self._attr_is_locked = locks[0].get("locked", False)
