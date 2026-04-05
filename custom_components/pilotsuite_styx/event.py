"""PilotSuite Styx Event Entities — HA-187.

Sync mit Core API: /api/v1/events/*
"""
from __future__ import annotations
import logging
from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup event entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreEventEntity(core_url)]
    async_add_entities(entities)

class CoreEventEntity(EventEntity):
    """Entity for Core API events."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Core Events"
        self._attr_unique_id = "pilotsuite_core_events"
        self._attr_event_types = ["state_changed", "service_executed", "automation_triggered"]
