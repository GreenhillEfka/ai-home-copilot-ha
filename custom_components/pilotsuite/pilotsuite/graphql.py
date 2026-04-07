"""PilotSuite Styx GraphQL — HA-253.

Sync mit Core API: /api/v1/graphql/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup GraphQL sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreGraphQLSensor(core_url)]
    async_add_entities(entities)

class CoreGraphQLSensor(SensorEntity):
    """Sensor for Core GraphQL endpoint."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite GraphQL"
        self._attr_unique_id = "pilotsuite_graphql"
        self._attr_native_value = "active"
    
    def update(self):
        """Update GraphQL status from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/graphql/schema", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = "active"
        else:
            self._attr_native_value = "inactive"
