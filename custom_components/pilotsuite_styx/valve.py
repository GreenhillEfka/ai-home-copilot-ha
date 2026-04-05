"""PilotSuite Styx Valve Entities — HA-199.

Sync mit Core API: /api/v1/blueprints/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup valve entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreBlueprintValve(core_url)]
    async_add_entities(entities)

class CoreBlueprintValve(ValveEntity):
    """Valve entity for Core blueprint control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Blueprint Valve"
        self._attr_unique_id = "pilotsuite_blueprint_valve"
        self._attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
        self._attr_is_closed = False
    
    def open_valve(self, **kwargs):
        """Open valve and trigger blueprint import."""
        self._attr_is_closed = False
        requests.post(f"{self._core_url}/api/v1/blueprints/import", json={"id": "open_valve_bp"}, timeout=5)
    
    def close_valve(self, **kwargs):
        """Close valve."""
        self._attr_is_closed = True
