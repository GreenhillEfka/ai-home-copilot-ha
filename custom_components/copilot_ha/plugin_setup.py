"""Plugin system integration for PilotSuite."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the PilotSuite plugin system."""
    # Initialize plugin system
    plugin_dir = Path(__file__).parent.parent / "plugins"
    
    # Create plugin directory if it doesn't exist
    plugin_dir.mkdir(exist_ok=True)
    
    # Import and setup plugin loader
    from .core.plugins import PluginLoader
    
    # Store plugin loader in hass data
    if "plugins" not in hass.data:
        hass.data["plugins"] = {}
    
    hass.data["plugins"]["loader"] = PluginLoader(plugin_dir, hass)
    
    # Load plugins
    loader = hass.data["plugins"]["loader"]
    loaded_count = await loader.load_all_plugins()
    
    _LOGGER.info("PilotSuite plugin system initialized with %d plugins", loaded_count)
    return True