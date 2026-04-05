"""PilotSuite Sensor Platform."""

from __future__ import annotations

import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PilotSuite sensor entities."""
    sensors = []
    host = config_entry.data.get("host", "http://localhost:5000")
    token = config_entry.data.get("token", "")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    async with aiohttp.ClientSession() as session:
        # Module sensors
        try:
            async with session.get(f"{host}/api/v1/sensors/modules", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for sensor_data in data.get("sensors", []):
                        sensors.append(PilotSuiteSensor(sensor_data))
        except Exception:
            pass
        
        # Zone sensors
        try:
            async with session.get(f"{host}/api/v1/sensors/zones", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for sensor_data in data.get("sensors", []):
                        sensors.append(PilotSuiteSensor(sensor_data))
        except Exception:
            pass
        
        # System sensors
        try:
            async with session.get(f"{host}/api/v1/sensors/system", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for sensor_data in data.get("sensors", []):
                        sensors.append(PilotSuiteSensor(sensor_data))
        except Exception:
            pass
    
    async_add_entities(sensors)


class PilotSuiteSensor(SensorEntity):
    """Representation of a PilotSuite sensor."""

    def __init__(self, sensor_data: dict) -> None:
        """Initialize the sensor."""
        self._attr_unique_id = sensor_data["unique_id"]
        self._attr_name = sensor_data["name"]
        self._attr_native_value = sensor_data["state"]
        self._attr_extra_state_attributes = sensor_data.get("attributes", {})
        self._attr_icon = sensor_data.get("icon", "mdi:puzzle")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self._attr_native_value
