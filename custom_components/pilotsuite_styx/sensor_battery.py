"""PilotSuite Styx Battery Sensors — HA-212.

Sync mit Core API: /api/v1/battery/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup battery sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreBatteryLevelSensor(core_url),
        CoreBatteryHealthSensor(core_url),
    ]
    async_add_entities(entities)

class CoreBatteryLevelSensor(SensorEntity):
    """Sensor for Core battery level."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Battery Level"
        self._attr_unique_id = "pilotsuite_battery_level"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_value = 0
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/battery/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("level", 0)

class CoreBatteryHealthSensor(SensorEntity):
    """Sensor for Core battery health."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Battery Health"
        self._attr_unique_id = "pilotsuite_battery_health"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_value = 100
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/battery/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("health", 100)
