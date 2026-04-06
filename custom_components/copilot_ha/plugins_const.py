"""Constants for PilotSuite plugin system."""

DOMAIN = "pilotsuite_plugins"

# Service names
SERVICE_LOAD_PLUGIN = "load_plugin"
SERVICE_UNLOAD_PLUGIN = "unload_plugin"
SERVICE_RELOAD_PLUGIN = "reload_plugin"
SERVICE_GET_PLUGINS = "get_plugins"

# Service schemas
SERVICE_LOAD_PLUGIN_SCHEMA = {
    "plugin_name": str,
    "plugin_path": str,
}

SERVICE_UNLOAD_PLUGIN_SCHEMA = {
    "plugin_name": str,
}

SERVICE_RELOAD_PLUGIN_SCHEMA = {
    "plugin_name": str,
}

# Default plugin directory
DEFAULT_PLUGIN_DIR = "/config/plugins"