"""PilotSuite Styx HA Integration — __init__.py (SOTA 2026).

Setup für:
1. Zone Automation Event Handler (state_changed → CORE)
2. Lovelace Cards Registry
3. Services Registry
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_CORE_URL, CONF_API_TOKEN
from .zone_automation_client import get_zone_automation_client
from .zone_automation_events import setup_zone_automation_events
from .cards.zone_automation_cards import register_cards

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "select", "button"]


async def async_setup(hass: HomeAssistant, config: Dict[str, Any]) -> bool:
    """Integration setupen (YAML)."""
    hass.data.setdefault(DOMAIN, {})
    
    # Register Lovelace Cards
    cards = register_cards()
    _LOGGER.info(f"Registered {len(cards)} Lovelace Cards")
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config Entry setupen."""
    core_url = entry.data.get(CONF_CORE_URL, "http://homeassistant.local:8909")
    api_token = entry.data.get(CONF_API_TOKEN, "")
    
    # Create client
    client = get_zone_automation_client(hass, core_url, api_token)
    
    # Store client
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "core_url": core_url,
    }
    
    # Setup Zone Automation Events
    try:
        event_handler = await setup_zone_automation_events(hass, client)
        hass.data[DOMAIN][entry.entry_id]["event_handler"] = event_handler
        _LOGGER.info("Zone Automation Events started")
    except Exception as e:
        _LOGGER.error(f"Zone Automation Events setup failed: {e}")
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await _register_services(hass, client)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config Entry entladen."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Stop event handler
        if entry.entry_id in hass.data[DOMAIN]:
            event_handler = hass.data[DOMAIN][entry.entry_id].get("event_handler")
            if event_handler:
                event_handler.stop()
            
            # Close client
            client = hass.data[DOMAIN][entry.entry_id].get("client")
            if client:
                await client.close()
            
            hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _register_services(hass: HomeAssistant, client) -> None:
    """Services registrieren."""
    
    async def set_neuron_mode(service_call):
        """Service: set_neuron_mode."""
        zone_id = service_call.data.get("zone_id")
        neuron_id = service_call.data.get("neuron_id")
        mode = service_call.data.get("mode")
        
        result = await client.set_neuron_mode(zone_id, neuron_id, mode)
        _LOGGER.info(f"set_neuron_mode: {result}")
    
    async def configure_light_automation(service_call):
        """Service: configure_light_automation."""
        zone_id = service_call.data.get("zone_id")
        config = {
            "enabled": service_call.data.get("enabled", True),
            "presence_trigger": service_call.data.get("presence_trigger", True),
            "brightness_threshold": service_call.data.get("brightness_threshold", 0.3),
            "presence_delay_seconds": service_call.data.get("presence_delay_seconds", 300),
            "time_dependent": service_call.data.get("time_dependent", True),
            "mood_dependent": service_call.data.get("mood_dependent", True),
        }
        
        result = await client.set_zone_config(zone_id, {"light": config})
        _LOGGER.info(f"configure_light_automation: {result}")
    
    hass.services.async_register(DOMAIN, "set_neuron_mode", set_neuron_mode)
    hass.services.async_register(DOMAIN, "configure_light_automation", configure_light_automation)
    
    _LOGGER.info("Registered services: set_neuron_mode, configure_light_automation")
