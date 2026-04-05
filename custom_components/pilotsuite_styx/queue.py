"""PilotSuite Styx Queue Entities — HA-192.

Sync mit Core API: /api/v1/jobs/*
"""
from __future__ import annotations
import logging
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
    """Setup queue sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreJobQueueSensor(core_url)]
    async_add_entities(entities)

class CoreJobQueueSensor(SensorEntity):
    """Sensor for Core job queue status."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Job Queue"
        self._attr_unique_id = "pilotsuite_job_queue"
        self._attr_native_value = 0
        self._attr_native_unit_of_measurement = "jobs"
