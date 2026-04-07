"""PilotSuite Styx Habitus Admin — HA-475.
Admin sensor for Habitus Zone management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        HabitusAdminSensor(core_url),
        HabitusLinkedDevicesSensor(core_url),
        HabitusRulesSensor(core_url)
    ])

class HabitusAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Habitus Zones"
        self._attr_unique_id = "pilotsuite_habitus_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/habitus/zones", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class HabitusLinkedDevicesSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Linked Devices"
        self._attr_unique_id = "pilotsuite_linked_devices"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/habitus/zones/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("total_device_links", 0)

class HabitusRulesSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Habitus Rules"
        self._attr_unique_id = "pilotsuite_habitus_rules"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/habitus/zones/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("total_habitus_rules", 0)
