"""PilotSuite Styx Irrigation Valve — HA-214.

Sync mit Core API: /api/v1/irrigation/*
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
    """Setup irrigation valve from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreIrrigationValve(core_url)]
    async_add_entities(entities)

class CoreIrrigationValve(ValveEntity):
    """Valve entity for irrigation control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Irrigation"
        self._attr_unique_id = "pilotsuite_irrigation"
        self._attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
        self._attr_is_closed = True
    
    def open_valve(self, **kwargs):
        """Start irrigation."""
        self._attr_is_closed = False
        requests.post(f"{self._core_url}/api/v1/irrigation/start", json={"zone": 1}, timeout=5)
    
    def close_valve(self, **kwargs):
        """Stop irrigation."""
        self._attr_is_closed = True
        requests.post(f"{self._core_url}/api/v1/irrigation/stop", timeout=5)
