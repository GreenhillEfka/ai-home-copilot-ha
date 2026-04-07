"""PilotSuite Styx Energy Sensors — HA-211.

Sync mit Core API: /api/v1/energy/*
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
    """Setup energy sensors from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [
        CoreEnergyConsumptionSensor(core_url),
        CoreEnergyCostSensor(core_url),
    ]
    async_add_entities(entities)

class CoreEnergyConsumptionSensor(SensorEntity):
    """Sensor for Core energy consumption."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Energy Consumption"
        self._attr_unique_id = "pilotsuite_energy_consumption"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_native_value = 0.0
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/energy/consumption", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("kwh_today", 0.0)

class CoreEnergyCostSensor(SensorEntity):
    """Sensor for Core energy cost."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Energy Cost"
        self._attr_unique_id = "pilotsuite_energy_cost"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_native_value = 0.0
    
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/energy/cost", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            self._attr_native_value = data.get("daily_cost", 0.0)
