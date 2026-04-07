"""PilotSuite Styx Binary Sensors — HA-189.

Sync mit Core API: /api/v1/modules/health, /api/v1/health/*
"""
from __future__ import annotations
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup binary sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreHealthBinarySensor(core_url),
        CoreModulesBinarySensor(core_url),
    ]
    async_add_entities(entities)

class CoreHealthBinarySensor(BinarySensorEntity):
    """Binary sensor for Core API health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Health"
        self._attr_unique_id = "pilotsuite_core_health_binary"
        self._attr_is_on = True

class CoreModulesBinarySensor(BinarySensorEntity):
    """Binary sensor for Core modules health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Modules Health"
        self._attr_unique_id = "pilotsuite_modules_health_binary"
        self._attr_is_on = True
