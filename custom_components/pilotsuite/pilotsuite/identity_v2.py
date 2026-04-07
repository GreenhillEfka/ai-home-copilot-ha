"""PilotSuite Styx Identity V2 — HA-433.
Auto-Sync Core: /api/v1/identity/v2/*
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)
async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([CoreIdentityV2Sensor(core_url)])
class CoreIdentityV2Sensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Identity V2"
        self._attr_unique_id = "pilotsuite_identity_v2"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/identity/v2/list", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = len(resp.json().get("identities", []))
