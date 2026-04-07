"""PilotSuite Styx Alarm Control Panel — HA-219.

Sync mit Core API: /api/v1/security/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature
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
    """Alarm control panel for Core security."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Security"
        self._attr_unique_id = "pilotsuite_security"
        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_HOME |
            AlarmControlPanelEntityFeature.ARM_AWAY |
            AlarmControlPanelEntityFeature.DISARM
        )
        self._attr_state = "disarmed"
    
    def alarm_arm_home(self, code=None):
        """Arm security in home mode."""
        requests.post(f"{self._core_url}/api/v1/security/arm", timeout=5)
        self._attr_state = "armed_home"
    
    def alarm_arm_away(self, code=None):
        """Arm security in away mode."""
        requests.post(f"{self._core_url}/api/v1/security/arm", timeout=5)
        self._attr_state = "armed_away"
    
    def alarm_disarm(self, code=None):
        """Disarm security."""
        requests.post(f"{self._core_url}/api/v1/security/disarm", timeout=5)
        self._attr_state = "disarmed"
    
    def update(self):
        """Update security state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/security/mode", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            mode = data.get("mode", "disarmed")
            self._attr_state = "armed_away" if mode == "armed" else "disarmed"
