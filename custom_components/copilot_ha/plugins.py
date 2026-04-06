"""Plugin integration for PilotSuite.

Provides plugin system integration with Home Assistant.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .core.plugins import PluginLoader

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PilotSuite plugin system."""
    # Initialize plugin system
    plugin_dir = Path(__file__).parent.parent / "plugins"
    
    # Create plugin directory if it doesn't exist
    plugin_dir.mkdir(exist_ok=True)
    
    # Store plugin loader in hass data
    hass.data[DOMAIN] = {
        "plugin_loader": PluginLoader(plugin_dir, hass),
    }
    
    # Load plugins
    loader = hass.data[DOMAIN]["plugin_loader"]
    loaded_count = await loader.load_all_plugins()
    
    _LOGGER.info("PilotSuite plugin system initialized with %d plugins", loaded_count)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PilotSuite plugin system from a config entry."""
    # Plugin system is already set up in async_setup
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop all plugins on unload
    if DOMAIN in hass.data and "plugin_loader" in hass.data[DOMAIN]:
        loader = hass.data[DOMAIN]["plugin_loader"]
        await loader.stop_all()
        del hass.data[DOMAIN]["plugin_loader"]
    
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)