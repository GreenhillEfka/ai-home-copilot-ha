"""PilotSuite Styx Alarm Control Panel — HA-207.

Sync mit Core API: /api/v1/alarm/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature, CodeFormat
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup alarm control panel from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreAlarmControlPanel(core_url)]
    async_add_entities(entities)

class CoreAlarmControlPanel(AlarmControlPanelEntity):
    """Alarm control panel for Core security system."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Alarm"
        self._attr_unique_id = "pilotsuite_alarm"
        self._attr_supported_features = AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.DISARM
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_state = "disarmed"
    
    def alarm_disarm(self, code: str | None = None) -> None:
        """Disarm alarm."""
        self._attr_state = "disarmed"
        requests.post(f"{self._core_url}/api/v1/alarm/disarm", timeout=5)
    
    def alarm_arm_home(self, code: str | None = None) -> None:
        """Arm alarm home."""
        self._attr_state = "armed_home"
        requests.post(f"{self._core_url}/api/v1/alarm/arm", json={"mode": "home"}, timeout=5)
    
    def alarm_arm_away(self, code: str | None = None) -> None:
        """Arm alarm away."""
        self._attr_state = "armed_away"
        requests.post(f"{self._core_url}/api/v1/alarm/arm", json={"mode": "away"}, timeout=5)
