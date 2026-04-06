"""Multi-Home Config Flow for PilotSuite Styx Integration.

Handles configuration of multi-home synchronization settings via the
Home Assistant UI. Allows users to:
- Register this home with a primary/remote PilotSuite instance
- Configure sync preferences (interval, conflict strategy)
- Manage cross-home automations
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_CORE_URL, DEFAULT_CORE_URL

logger = logging.getLogger(__name__)

# Config keys
CONF_HOME_ID = "home_id"
CONF_HOME_NAME = "home_name"
CONF_HOME_TYPE = "home_type"
CONF_IS_PRIMARY = "is_primary"
CONF_SYNC_INTERVAL = "sync_interval"
CONF_CONFLICT_STRATEGY = "conflict_strategy"
CONF_SHARED_SECRET = "shared_secret"

# Home types for selection
HOME_TYPES = {
    "primary": "Primary Home (Hauptwohnung)",
    "vacation": "Vacation Home (Ferienhaus)",
    "office": "Office (Büro)",
    "secondary": "Secondary Home",
}

# Conflict resolution strategies
CONFLICT_STRATEGIES = {
    "last_write_wins": "Last Write Wins (newest timestamp)",
    "primary_wins": "Primary Home Always Wins",
    "merge": "Smart Merge (combine changes)",
    "manual": "Manual Resolution Required",
}


class MultiHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle multi-home configuration flow."""

    VERSION = 2
    MINOR_VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self._config: dict[str, Any] = {}
        self._sync_available: bool = False
        self._sync_error: Optional[str] = None

    async def async_step_user(
        self,
        user_input: Optional[dict[str, Any]] = None,
    ) -> FlowResult:
        """Handle initial user step."""
        errors = {}

        if user_input is not None:
            # Validate core URL
            core_url = user_input.get(CONF_CORE_URL, DEFAULT_CORE_URL).rstrip("/")
            if not core_url:
                errors[CONF_CORE_URL] = "url_required"
            elif not core_url.startswith(("http://", "https://")):
                errors[CONF_CORE_URL] = "invalid_url"
            else:
                # Test connectivity
                self._config[CONF_CORE_URL] = core_url
                connectivity_ok, error = await self._test_connectivity(core_url)

                if connectivity_ok:
                    self._sync_available = True
                    return await self.async_step_home_config()
                else:
                    errors["base"] = f"Cannot connect: {error}"
                    self._sync_error = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CORE_URL, default=DEFAULT_CORE_URL): str,
            }),
            errors=errors,
            description_placeholders={
                "default_url": DEFAULT_CORE_URL,
                "error": self._sync_error or "",
            },
        )

    async def async_step_home_config(
        self,
        user_input: Optional[dict[str, Any]] = None,
    ) -> FlowResult:
        """Configure home identity and sync settings."""
        errors = {}

        if user_input is not None:
            home_id = user_input.get(CONF_HOME_ID, "").strip()
            home_name = user_input.get(CONF_HOME_NAME, "").strip()

            if not home_id:
                errors[CONF_HOME_ID] = "home_id_required"
            elif not home_name:
                errors[CONF_HOME_NAME] = "home_name_required"
            else:
                self._config.update({
                    CONF_HOME_ID: home_id,
                    CONF_HOME_NAME: home_name,
                    CONF_HOME_TYPE: user_input.get(CONF_HOME_TYPE, "primary"),
                    CONF_IS_PRIMARY: user_input.get(CONF_IS_PRIMARY, False),
                    CONF_SYNC_INTERVAL: user_input.get(CONF_SYNC_INTERVAL, 300),
                    CONF_CONFLICT_STRATEGY: user_input.get(CONF_CONFLICT_STRATEGY, "last_write_wins"),
                })

                # Optional: shared secret for encrypted sync
                if user_input.get(CONF_SHARED_SECRET):
                    self._config[CONF_SHARED_SECRET] = user_input[CONF_SHARED_SECRET]

                return await self.async_step_confirm()

        return self.async_show_form(
            step_id="home_config",
            data_schema=vol.Schema({
                vol.Required(CONF_HOME_ID, default=self._generate_home_id()): str,
                vol.Required(CONF_HOME_NAME): str,
                vol.Required(CONF_HOME_TYPE, default="primary"): vol.In(HOME_TYPES),
                vol.Optional(CONF_IS_PRIMARY, default=False): bool,
                vol.Optional(CONF_SYNC_INTERVAL, default=300): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=60, max=3600),
                ),
                vol.Optional(CONF_CONFLICT_STRATEGY, default="last_write_wins"): vol.In(CONFLICT_STRATEGIES),
                vol.Optional(CONF_SHARED_SECRET): str,
            }),
            errors=errors,
            description_placeholders={
                "home_types": ", ".join(HOME_TYPES.values()),
            },
        )

    async def async_step_confirm(
        self,
        user_input: Optional[dict[str, Any]] = None,
    ) -> FlowResult:
        """Confirm and finalize configuration."""
        if user_input is not None or True:
            # Check for existing entry
            await self.async_set_unique_id(self._config.get(CONF_HOME_ID, "multihome"))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Multi-Home: {self._config.get(CONF_HOME_NAME, 'Home')}",
                data=self._config,
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "home_name": self._config.get(CONF_HOME_NAME, "Unknown"),
                "home_type": HOME_TYPES.get(self._config.get(CONF_HOME_TYPE, "primary"), "Unknown"),
                "core_url": self._config.get(CONF_CORE_URL, "Unknown"),
            },
        )

    async def async_step_reconfigure(
        self,
        user_input: Optional[dict[str, Any]] = None,
    ) -> FlowResult:
        """Handle reconfiguration of existing entry."""
        entry = self._get_reconfigure_entry()
        self._config = dict(entry.data)

        if user_input is not None:
            self._config.update(user_input)
            return self.async_update_reload_and_abort(
                entry,
                data=self._config,
                reason="reconfigure_successful",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_CORE_URL, default=self._config.get(CONF_CORE_URL, DEFAULT_CORE_URL)): str,
                vol.Required(CONF_HOME_NAME, default=self._config.get(CONF_HOME_NAME, "")): str,
                vol.Required(CONF_HOME_TYPE, default=self._config.get(CONF_HOME_TYPE, "primary")): vol.In(HOME_TYPES),
                vol.Optional(CONF_SYNC_INTERVAL, default=self._config.get(CONF_SYNC_INTERVAL, 300)): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=60, max=3600),
                ),
                vol.Optional(CONF_CONFLICT_STRATEGY, default=self._config.get(CONF_CONFLICT_STRATEGY, "last_write_wins")): vol.In(CONFLICT_STRATEGIES),
            }),
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def _test_connectivity(self, core_url: str) -> tuple[bool, Optional[str]]:
        """Test connectivity to the PilotSuite Core API.

        Returns (success, error_message).
        """
        import aiohttp
        import asyncio

        test_url = f"{core_url}/api/v1/sync/health"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("ok"):
                            return True, None
                        return False, "API returned error"
                    return False, f"HTTP {resp.status}"
        except asyncio.TimeoutError:
            return False, "Connection timeout"
        except aiohttp.ClientError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def _generate_home_id(self) -> str:
        """Generate a suggested home ID based on hostname."""
        import socket
        import hashlib

        hostname = socket.gethostname()
        hash_suffix = hashlib.sha256(hostname.encode()).hexdigest()[:8]
        return f"home-{hash_suffix}"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow handler."""
        return MultiHomeOptionsFlow(config_entry)


class MultiHomeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for multi-home configuration."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: Optional[dict[str, Any]] = None,
    ) -> FlowResult:
        """Manage options."""
        errors = {}

        if user_input is not None:
            # Validate sync interval
            interval = user_input.get(CONF_SYNC_INTERVAL, 300)
            if interval < 60 or interval > 3600:
                errors[CONF_SYNC_INTERVAL] = "interval_range"
            else:
                return self.async_create_entry(
                    title="",
                    data=user_input,
                )

        current = dict(self.config_entry.data)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SYNC_INTERVAL, default=current.get(CONF_SYNC_INTERVAL, 300)): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=60, max=3600),
                ),
                vol.Optional(CONF_CONFLICT_STRATEGY, default=current.get(CONF_CONFLICT_STRATEGY, "last_write_wins")): vol.In(CONFLICT_STRATEGIES),
            }),
            errors=errors,
        )
