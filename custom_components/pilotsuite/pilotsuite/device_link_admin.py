"""PilotSuite Styx Device Link Admin — HA-477.
Admin sensors for Device Link management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        DeviceLinkAdminSensor(core_url),
        DeviceLinkByDomainSensor(core_url),
        DeviceLinkZonedSensor(core_url)
    ])

class DeviceLinkAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Device Links"
        self._attr_unique_id = "pilotsuite_device_links_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/devices/links", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class DeviceLinkByDomainSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Domains"
        self._attr_unique_id = "pilotsuite_device_domains"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/devices/links/summary", timeout=5)
        if resp.status_code == 200:
            domains = resp.json().get("summary", {}).get("by_domain", {})
            self._attr_native_value = len(domains)

class DeviceLinkZonedSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Zoned Devices"
        self._attr_unique_id = "pilotsuite_zoned_devices"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/devices/links/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("links_with_zone", 0)
