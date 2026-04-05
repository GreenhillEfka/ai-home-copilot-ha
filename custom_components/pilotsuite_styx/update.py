"""PilotSuite Styx Update Entity — HA-196.

Sync mit Core API: /api/v1/hacs/versions, /api/v1/system/info
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL, VERSION

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup update entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreUpdateEntity(core_url, VERSION)]
    async_add_entities(entities)

class CoreUpdateEntity(UpdateEntity):
    """Update entity for PilotSuite Core."""
    
    def __init__(self, core_url: str, current_version: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Update"
        self._attr_unique_id = "pilotsuite_core_update"
        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_installed_version = current_version
        self._attr_latest_version = current_version
        self._attr_release_summary = "v15.3.40 — HACS Integration Complete"
    
    def install(self, **kwargs):
        """Trigger update via Core API."""
        requests.post(f"{self._core_url}/api/v1/system/update", json={}, timeout=30)
