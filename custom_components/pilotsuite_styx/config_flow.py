"""Config Flow for PilotSuite Styx — HA-182."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_CORE_URL, DEFAULT_CORE_URL, DOMAIN


class PilotSuiteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle PilotSuite config flow."""

    VERSION = 2
    MINOR_VERSION = 0

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            core_url = user_input.get(CONF_CORE_URL, DEFAULT_CORE_URL).rstrip("/")
            if not core_url:
                errors[CONF_CORE_URL] = "url_required"
            elif not core_url.startswith(("http://", "https://")):
                errors[CONF_CORE_URL] = "invalid_url"

            if not errors:
                return self.async_create_entry(
                    title="PilotSuite Styx",
                    data={CONF_CORE_URL: core_url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CORE_URL, default=DEFAULT_CORE_URL): str,
            }),
            errors=errors,
            description_placeholders={
                "default_url": DEFAULT_CORE_URL,
            },
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PilotSuite."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}

        if user_input is not None:
            core_url = user_input.get(CONF_CORE_URL, "").rstrip("/")
            if not core_url:
                errors[CONF_CORE_URL] = "url_required"
            elif not core_url.startswith(("http://", "https://")):
                errors[CONF_CORE_URL] = "invalid_url"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={CONF_CORE_URL: core_url},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_CORE_URL,
                    default=self.config_entry.data.get(CONF_CORE_URL, DEFAULT_CORE_URL),
                ): str,
            }),
            errors=errors,
        )
