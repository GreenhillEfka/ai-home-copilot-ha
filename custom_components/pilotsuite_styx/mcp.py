"""PilotSuite Styx MCP — HA-242.

Sync mit Core API: /api/v1/mcp/*, /api/v1/tools/*
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
    """Setup MCP switch from config entry."""
    core_url = config_entry.data.get(CONF_CORE_URL, "http://localhost:8909")
    entities = [CoreMCPSwitch(core_url)]
    async_add_entities(entities)

class CoreMCPSwitch(SwitchEntity):
    """Switch entity for MCP server control."""
    def __init__(self, core_url: str):
        self._core_url = core_url
        self._attr_name = "PilotSuite MCP"
        self._attr_unique_id = "pilotsuite_mcp"
        self._attr_is_on = False
    
    def turn_on(self, **kwargs):
        """Connect MCP server."""
        requests.post(f"{self._core_url}/api/v1/mcp/connect", json={"server": "local"}, timeout=5)
        self._attr_is_on = True
    
    def turn_off(self, **kwargs):
        """Disconnect MCP server."""
        self._attr_is_on = False
    
    def update(self):
        """Update MCP state from Core."""
        resp = requests.get(f"{self._core_url}/api/v1/mcp/servers", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            servers = data.get("servers", [])
            self._attr_is_on = any(s.get("connected") for s in servers)
