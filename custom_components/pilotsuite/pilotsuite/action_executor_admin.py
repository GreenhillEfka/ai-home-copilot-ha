"""PilotSuite Styx Action Executor Admin — HA-480.
Admin sensors for Action Executor management.
"""
from __future__ import annotations
import logging, requests
from homeassistant.components.sensor import SensorEntity
from .const import CONF_CORE_URL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    async_add_entities([
        ActionExecutorAdminSensor(core_url),
        ActionExecutionsSensor(core_url),
        ActionWithScriptSensor(core_url)
    ])

class ActionExecutorAdminSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Actions"
        self._attr_unique_id = "pilotsuite_actions_admin"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/actions", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("count", 0)

class ActionExecutionsSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Total Executions"
        self._attr_unique_id = "pilotsuite_action_executions"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/actions/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("total_executions", 0)

class ActionWithScriptSensor(SensorEntity):
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Linked Scripts"
        self._attr_unique_id = "pilotsuite_actions_linked_scripts"
        self._attr_native_value = 0
    def update(self):
        resp = requests.get(f"{self._core_url}/api/v1/actions/summary", timeout=5)
        if resp.status_code == 200:
            self._attr_native_value = resp.json().get("summary", {}).get("actions_with_script", 0)
