"""PilotSuite Styx Lawn Mower Entities — HA-201.

Sync mit Core API: /api/v1/automation/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.lawn_mower import LawnMowerEntity, LawnMowerActivity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup lawn mower entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreAutomationLawnMower(core_url)]
    async_add_entities(entities)

class CoreAutomationLawnMower(LawnMowerEntity):
    """Lawn mower entity for Core automation."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Automation Mower"
        self._attr_unique_id = "pilotsuite_automation_mower"
        self._attr_activity = LawnMowerActivity.DOCKED
    
    def start_mowing(self, **kwargs):
        """Start mowing and trigger automation."""
        self._attr_activity = LawnMowerActivity.MOWING
        requests.post(f"{self._core_url}/api/v1/automation/create", json={"id": "start_mowing"}, timeout=5)
    
    def dock(self, **kwargs):
        """Dock mower."""
        self._attr_activity = LawnMowerActivity.DOCKED
        requests.post(f"{self._core_url}/api/v1/automation/create", json={"id": "dock_mower"}, timeout=5)
