"""PilotSuite Styx Power Sensors — HA-209.

Sync mit Core API: /api/v1/power/*, /api/v1/ups/*
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
    """Setup power sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreVoltageSensor(core_url),
        CorePowerConsumptionSensor(core_url),
        CoreUPSBatterySensor(core_url),
    ]
    async_add_entities(entities)

class CoreVoltageSensor(SensorEntity):
    """Sensor for Core voltage."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Voltage"
        self._attr_unique_id = "pilotsuite_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "V"
        self._attr_native_value = 230.0
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/power/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("voltage", 230.0)

class CorePowerConsumptionSensor(SensorEntity):
    """Sensor for Core power consumption."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Power Consumption"
        self._attr_unique_id = "pilotsuite_power_consumption"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_native_value = 0.0
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/power/consumption", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("watts", 0.0)

class CoreUPSBatterySensor(SensorEntity):
    """Sensor for Core UPS battery."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite UPS Battery"
        self._attr_unique_id = "pilotsuite_ups_battery"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "%"
        self._attr_native_value = 100
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/ups/state", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("battery", 100)
