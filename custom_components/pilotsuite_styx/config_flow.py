"""Config Flow for PilotSuite Styx — HA-182."""
from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_CORE_URL

class PilotSuiteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle PilotSuite config flow."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="PilotSuite Styx", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CORE_URL, default="http://localhost:8909"): str,
            })
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_CORE_URL, default=self.config_entry.data.get(CONF_CORE_URL)): str,
            })
        )
