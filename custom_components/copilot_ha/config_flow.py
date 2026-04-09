"""Legacy config-flow bridge for old copilot_ha handler references."""

from homeassistant import config_entries
from custom_components.pilotsuite.config_flow import ConfigFlow as PilotSuiteConfigFlow


class ConfigFlow(PilotSuiteConfigFlow, domain="copilot_ha"):
    """Bridge old copilot_ha setup-flow calls to the current PilotSuite flow."""

    VERSION = PilotSuiteConfigFlow.VERSION
