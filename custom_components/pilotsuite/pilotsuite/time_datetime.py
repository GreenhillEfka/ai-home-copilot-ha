"""PilotSuite Styx Time & DateTime Entities — HA-229.

Sync mit Core API: /api/v1/time/*, /api/v1/datetime/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.time import TimeEntity
from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL
from datetime import time, datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup time and datetime entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreTimeEntity(core_url, "Wake Time", "wake_time"),
        CoreDateTimeEntity(core_url, "Schedule DateTime", "schedule_datetime"),
    ]
    async_add_entities(entities)

class CoreTimeEntity(TimeEntity):
    """Time entity for Core."""
    def __init__(self, core_url: str, name: str, id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_{id}"
        self._attr_native_value = time(8, 0)
    
    def set_value(self, value):
        requests.post(f"{self._core_url}/api/v1/time/set", json={"time": value.isoformat()}, timeout=5)
        self._attr_native_value = value

class CoreDateTimeEntity(DateTimeEntity):
    """DateTime entity for Core."""
    def __init__(self, core_url: str, name: str, id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_{id}"
        self._attr_native_value = datetime.now()
    
    def set_value(self, value):
        requests.post(f"{self._core_url}/api/v1/datetime/set", json={"datetime": value.isoformat()}, timeout=5)
        self._attr_native_value = value
