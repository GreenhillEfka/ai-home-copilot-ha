"""PilotSuite Styx Agent — HA-243.

Sync mit Core API: /api/v1/agents/*, /api/v1/workers/*
"""
from __future__ import annotations
import logging
import requests
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import CONF_CORE_URL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup agent switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreAgentSwitch(core_url)]
    async_add_entities(entities)

class CoreAgentSwitch(SwitchEntity):
    """Switch entity for agent control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite Agent"
        self._attr_unique_id = "pilotsuite_agent"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Spawn agent."""
        requests.post(f"{self._core_url}/api/v1/agents/spawn", json={"type": "assistant"}, timeout=5)
        self._attr_is_on = True
    
    def turn_off(self, **kwargs):
        """Stop agent."""
        self._attr_is_on = False
    
    def update(self):
        """Update agent state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/agents/list", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            agents = data.get("agents", [])
            self._attr_is_on = any(a.get("active") for a in agents)
