"""PilotSuite Styx Text & Date Entities — HA-228.

Sync mit Core API: /api/v1/text/*, /api/v1/dates/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.text import TextEntity
from homeassistant.components.date import DateEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup text and date entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreTextEntity(core_url, "Message", "message"),
        CoreDateEntity(core_url, "Schedule Date", "schedule_date"),
    ]
    async_add_entities(entities)

class CoreTextEntity(TextEntity):
    """Text entity for Core."""
    def __init__(self, core_url: str, name: str, id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_{id}"
        self._attr_native_value = ""
    
    def set_value(self, value):
        requests.post(f"{self._core_url}/api/v1/text/set", json={"value": value}, timeout=5)
        self._attr_native_value = value

class CoreDateEntity(DateEntity):
    """Date entity for Core."""
    def __init__(self, core_url: str, name: str, id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_{id}"
        from datetime import date
        self._attr_native_value = date.today()
    
    def set_value(self, value):
        requests.post(f"{self._core_url}/api/v1/dates/set", json={"date": value.isoformat()}, timeout=5)
        self._attr_native_value = value
