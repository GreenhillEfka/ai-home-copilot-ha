"""PilotSuite Styx Script Entity — HA-234.

Sync mit Core API: /api/v1/scripts/*, /api/v1/actions/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.script import ScriptEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup script entity from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreScriptEntity(core_url)]
    async_add_entities(entities)

class CoreScriptEntity(ScriptEntity):
    """Script entity for Core."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Script"
        self._attr_unique_id = "pilotsuite_script"
    
    async def async_run(self, variables=None, context=None):
        """Run script."""
        requests.post(f"{self._core_url}/api/v1/scripts/run", json={"script_id": self._attr_unique_id}, timeout=5)
