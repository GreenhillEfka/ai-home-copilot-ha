"""PilotSuite Styx Automation — HA-233.

Sync mit Core API: /api/v1/automations/*, /api/v1/rules/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import SwitchEntity
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup automation entities from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreAutomationSwitch(core_url, "Scene Automation", "scene_auto")]
    async_add_entities(entities)

class CoreAutomationSwitch(SwitchEntity):
    """Switch entity for automation control."""
    def __init__(self, core_url: str, name: str, id: str):
        self._core_url = core_url
        self._attr_name = f"PilotSuite {name}"
        self._attr_unique_id = f"pilotsuite_{id}"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Enable automation."""
        requests.post(f"{self._core_url}/api/v1/automations/create", json={"name": self._attr_unique_id, "enabled": True}, timeout=5)
        self._attr_is_on = True
    
    def turn_off(self, **kwargs):
        """Disable automation."""
        self._attr_is_on = False
    
    def update(self):
        """Update automation state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/automations/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            automations = data.get("automations", [])
            for auto in automations:
                if auto.get("id") == self._attr_unique_id:
                    self._attr_is_on = auto.get("enabled", False)
