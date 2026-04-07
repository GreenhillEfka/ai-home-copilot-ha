"""PilotSuite Styx Number Entities — HA-197.

Sync mit Core API: /api/v1/system/*, /api/v1/ping/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup number entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CorePollingIntervalNumber(core_url)]
    async_add_entities(entities)

class CorePollingIntervalNumber(NumberEntity):
    """Number entity for Core polling interval."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "Core Polling Interval"
        self._attr_unique_id = "pilotsuite_polling_interval"
        self._attr_native_value = 30
        self._attr_native_min_value = 5
        self._attr_native_max_value = 300
        self._attr_native_step = 5
        self._attr_native_unit_of_measurement = "s"
    
    def set_native_value(self, value: float) -> None:
        """Set polling interval and sync with Core."""
        self._attr_native_value = value
        requests.post(f"{self._core_url}/api/v1/system/config", json={"polling_interval": int(value)}, timeout=5)
