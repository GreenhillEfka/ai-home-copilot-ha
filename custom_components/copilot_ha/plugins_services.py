"""Services for PilotSuite plugin system.

Provides Home Assistant services for plugin management.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util.json import JsonObjectType

from .plugins_const import (
    DEFAULT_PLUGIN_DIR,
    DOMAIN,
    SERVICE_GET_PLUGINS,
    SERVICE_LOAD_PLUGIN,
    SERVICE_RELOAD_PLUGIN,
    SERVICE_UNLOAD_PLUGIN,
    SERVICE_LOAD_PLUGIN_SCHEMA,
    SERVICE_RELOAD_PLUGIN_SCHEMA,
    SERVICE_UNLOAD_PLUGIN_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_LOAD_PLUGIN_SCHEMA = vol.Schema({
    vol.Required("plugin_name"): cv.string,
    vol.Optional("plugin_path", default=DEFAULT_PLUGIN_DIR): cv.string,
})

SERVICE_UNLOAD_PLUGIN_SCHEMA = vol.Schema({
    vol.Required("plugin_name"): cv.string,
})

SERVICE_RELOAD_PLUGIN_SCHEMA = vol.Schema({
    vol.Required("plugin_name"): cv.string,
})

SERVICE_GET_PLUGINS_SCHEMA = vol.Schema({})


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up plugin services."""
    
    async def load_plugin(call: ServiceCall) -> None:
        """Load a plugin dynamically."""
        plugin_name = call.data["plugin_name"]
        plugin_path = Path(call.data["plugin_path"])
        
        if DOMAIN not in hass.data or "plugin_loader" not in hass.data[DOMAIN]:
            _LOGGER.error("Plugin system not initialized")
            return
        
        loader = hass.data[DOMAIN]["plugin_loader"]
        
        # Load manifest
        manifest_path = plugin_path / plugin_name / "plugin.json"
        if not manifest_path.exists():
            _LOGGER.error("Plugin manifest not found: %s", manifest_path)
            return
        
        from .core.plugins import PluginManifest
        manifest = PluginManifest.from_directory(plugin_path / plugin_name)
        if not manifest:
            _LOGGER.error("Invalid plugin manifest: %s", plugin_name)
            return
        
        # Load plugin
        loaded_plugin = await loader.load_plugin(manifest)
        if loaded_plugin:
            _LOGGER.info("Plugin loaded successfully: %s", plugin_name)
        else:
            _LOGGER.error("Failed to load plugin: %s", plugin_name)
    
    async def unload_plugin(call: ServiceCall) -> None:
        """Unload a plugin."""
        plugin_name = call.data["plugin_name"]
        
        if DOMAIN not in hass.data or "plugin_loader" not in hass.data[DOMAIN]:
            _LOGGER.error("Plugin system not initialized")
            return
        
        loader = hass.data[DOMAIN]["plugin_loader"]
        success = await loader.unload_plugin(plugin_name)
        
        if success:
            _LOGGER.info("Plugin unloaded successfully: %s", plugin_name)
        else:
            _LOGGER.error("Failed to unload plugin: %s", plugin_name)
    
    async def reload_plugin(call: ServiceCall) -> None:
        """Reload a plugin."""
        plugin_name = call.data["plugin_name"]
        
        if DOMAIN not in hass.data or "plugin_loader" not in hass.data[DOMAIN]:
            _LOGGER.error("Plugin system not initialized")
            return
        
        loader = hass.data[DOMAIN]["plugin_loader"]
        success = await loader.reload_plugin(plugin_name)
        
        if success:
            _LOGGER.info("Plugin reloaded successfully: %s", plugin_name)
        else:
            _LOGGER.error("Failed to reload plugin: %s", plugin_name)
    
    async def get_plugins(call: ServiceCall) -> JsonObjectType:
        """Get plugin information."""
        if DOMAIN not in hass.data or "plugin_loader" not in hass.data[DOMAIN]:
            return {"error": "Plugin system not initialized"}
        
        loader = hass.data[DOMAIN]["plugin_loader"]
        diagnostics = await loader.registry.get_diagnostics()
        
        return {
            "plugins": diagnostics,
            "count": len(diagnostics),
            "capabilities": dict(loader.registry._capabilities),
        }
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_LOAD_PLUGIN,
        load_plugin,
        schema=SERVICE_LOAD_PLUGIN_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNLOAD_PLUGIN,
        unload_plugin,
        schema=SERVICE_UNLOAD_PLUGIN_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD_PLUGIN,
        reload_plugin,
        schema=SERVICE_RELOAD_PLUGIN_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_PLUGINS,
        get_plugins,
        schema=SERVICE_GET_PLUGINS_SCHEMA,
        supports_response=True,
    )
    
    _LOGGER.info("Plugin services registered for domain: %s", DOMAIN)