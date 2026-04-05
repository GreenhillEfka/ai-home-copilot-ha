"""Config Flow for PilotSuite."""

from __future__ import annotations

import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN


class PilotSuiteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PilotSuite."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Validate connection
            host = user_input["host"]
            token = user_input.get("token", "")
            
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"Authorization": f"Bearer {token}"} if token else {}
                    async with session.get(f"{host}/api/v1/sensors/system", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            return self.async_create_entry(title="PilotSuite", data=user_input)
                        elif resp.status == 401:
                            errors["base"] = "invalid_auth"
                        else:
                            errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("host", default="http://localhost:5000"): str,
                    vol.Optional("token"): str,
                }
            ),
            errors=errors,
        )
