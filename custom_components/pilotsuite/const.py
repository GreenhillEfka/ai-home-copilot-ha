"""Constants for PilotSuite Styx Integration."""
from homeassistant.const import Platform

DOMAIN = "pilotsuite_styx"
CONF_CORE_URL = "core_url"
DEFAULT_CORE_URL = "http://localhost:8909"
VERSION = "16.1.0"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SWITCH,
]
