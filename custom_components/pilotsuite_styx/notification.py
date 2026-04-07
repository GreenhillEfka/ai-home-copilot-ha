"""PilotSuite Styx Notification — HA-265.

Sync mit Core API: /api/v1/notifications/*
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
    """Setup notification sensor from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreNotificationSensor(core_url)]
    async_add_entities(entities)

class CoreNotificationSensor(SensorEntity):
    """Sensor for Core notification count."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Notifications"
        self._attr_unique_id = "pilotsuite_notifications"
        self._attr_native_value = 0
    
    def update(self):
        """Update notification count from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/notifications/count", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("count", 0)
