"""Config flow for PilotSuite integration.

This is the thin coordinator module. Heavy logic lives in:
- config_helpers.py         - CSV utils, constants
- config_schema_builders.py - All schema builder functions
- config_wizard_steps.py    - Wizard step handlers
- config_zones_flow.py      - Zone management + helpers
- config_options_flow.py    - OptionsFlowHandler
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .config_helpers import (
    STEP_DISCOVERY,
    STEP_ZONES,
    STEP_ZONE_ENTITIES,
    STEP_ENTITIES,
    STEP_FEATURES,
    STEP_NETWORK,
    STEP_MODULES,
    STEP_REVIEW,
    merge_config_data,
    validate_input,
    discover_reachable_core_endpoint,
    fetch_setup_token,
)
from .config_options_flow import OptionsFlowHandler  # noqa: F401 - used by HA via async_get_options_flow
from .config_schema_builders import build_config_flow_connection_schema
from .config_wizard_steps import (
    build_discovery_form,
    build_zones_form,
    build_zone_entities_form,
    build_entities_form,
    build_features_form,
    build_network_form,
    build_review_form,
    process_discovery_input,
    process_zones_input,
    process_zone_entities_input,
    process_entities_input,
    process_features_input,
    process_network_input,
    build_final_config,
)
from .config_zones_flow import get_zone_entity_suggestions
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TEST_LIGHT,
    CONF_TOKEN,
    CONF_ENTITY_PROFILE,
    DEFAULT_ENTITY_PROFILE,
    ENTITY_PROFILES,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DOMAIN,
    INTEGRATION_UNIQUE_ID,
)
from .setup_wizard import SetupWizard

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    # Shared pending reconfigure data (accumulates across steps before final commit)
    _reconfigure_data: dict = {}

    async def get_zone_entity_suggestions(self, zone_name: str) -> dict:
        """Get entity suggestions for a zone."""
        return await get_zone_entity_suggestions(self.hass, zone_name)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Initial step - show main menu with Zero Config, Quick Start, or Manual."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_show_menu(
            step_id="user",
            menu_options=["zero_config", "quick_start", "manual_setup"],
            description_placeholders={
                "description": "PilotSuite Setup\n\n"
                "Choose your setup method:\n\n"
                "Zero Config: Install and start immediately with smart defaults. "
                "PilotSuite discovers your devices automatically and asks for "
                "improvements later through conversation.\n\n"
                "Quick Start: Guided wizard to configure zones and devices (~2 min).\n\n"
                "Manual Setup: Expert configuration with full control.\n"
            },
        )

    async def async_step_zero_config(self, user_input: dict | None = None) -> FlowResult:
        """Zero Config - instant start with Styx defaults.

        Tries Core connectivity first; if unreachable, creates the entry
        anyway (governance-first: the user can reconfigure later) but
        logs a clear warning so it shows up in the system log.
        """
        resolved = await discover_reachable_core_endpoint(
            self.hass,
            preferred_host=DEFAULT_HOST,
            preferred_port=DEFAULT_PORT,
        )
        host, port = resolved if resolved else (DEFAULT_HOST, DEFAULT_PORT)
        if resolved is None:
            _LOGGER.warning(
                "Zero-config: no reachable Core endpoint auto-detected; using defaults %s:%s",
                DEFAULT_HOST,
                DEFAULT_PORT,
            )

        # Auto-fetch token from Core (1-Key-Flow)
        token = ""
        if host and port:
            token = await fetch_setup_token(self.hass, host, port)

        config = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_TOKEN: token,
            CONF_ENTITY_PROFILE: DEFAULT_ENTITY_PROFILE,
            "assistant_name": "Styx",
        }

        # Best-effort connectivity check (non-blocking)
        try:
            await validate_input(self.hass, config)
            _LOGGER.info("Zero-config: Core reachable at %s:%s (token=%s)",
                         host, port, "auto" if token else "none")
        except Exception:
            _LOGGER.warning(
                "Zero-config: Core Add-on not reachable at %s:%s — "
                "integration will start anyway. Reconfigure via "
                "Settings > Integrations > PilotSuite > Configure",
                host,
                port,
            )

        await self.async_set_unique_id(INTEGRATION_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        title = "Styx — PilotSuite"
        return self.async_create_entry(title=title, data=config)

    async def async_step_quick_start(self, user_input: dict | None = None) -> FlowResult:
        """Quick Start - guided wizard with smart defaults."""
        return await self.async_step_wizard(user_input)

    async def async_step_manual_setup(self, user_input: dict | None = None) -> FlowResult:
        """Manual setup - direct configuration form."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Best-effort connectivity check — warn but always create entry
            try:
                await validate_input(self.hass, user_input)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "Core not reachable at %s:%s (%s) — "
                    "creating entry anyway, will retry automatically",
                    user_input.get(CONF_HOST),
                    user_input.get(CONF_PORT),
                    err,
                )

            if self.source == config_entries.SOURCE_REAUTH:
                reauth_entry = self.hass.config_entries.async_get_entry(self.context.get("entry_id"))
                if reauth_entry is not None:
                    updated = {**reauth_entry.data, **user_input}
                    updated.setdefault(CONF_ENTITY_PROFILE, DEFAULT_ENTITY_PROFILE)
                    self.hass.config_entries.async_update_entry(reauth_entry, data=updated)
                    await self.hass.config_entries.async_reload(reauth_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            # Auto-fetch token if user left it empty
            if not str(user_input.get(CONF_TOKEN) or "").strip():
                user_input[CONF_TOKEN] = await fetch_setup_token(
                    self.hass,
                    str(user_input.get(CONF_HOST, DEFAULT_HOST)),
                    int(user_input.get(CONF_PORT, DEFAULT_PORT)),
                )

            name = user_input.get("assistant_name", "Styx")
            title = f"{name} — PilotSuite ({user_input[CONF_HOST]}:{user_input[CONF_PORT]})"
            user_input.setdefault(CONF_ENTITY_PROFILE, DEFAULT_ENTITY_PROFILE)
            await self.async_set_unique_id(INTEGRATION_UNIQUE_ID)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=title, data=user_input)

        discovered = await discover_reachable_core_endpoint(
            self.hass,
            preferred_host=DEFAULT_HOST,
            preferred_port=DEFAULT_PORT,
        )
        default_host, default_port = discovered if discovered else (DEFAULT_HOST, DEFAULT_PORT)

        schema = vol.Schema(
            {
                vol.Optional("assistant_name", default="Styx"): str,
                **build_config_flow_connection_schema(
                    {
                        CONF_HOST: default_host,
                        CONF_PORT: default_port,
                    }
                ),
                vol.Optional(CONF_ENTITY_PROFILE, default=DEFAULT_ENTITY_PROFILE): vol.In(ENTITY_PROFILES),
            }
        )

        return self.async_show_form(
            step_id="manual_setup",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "description": "Enter your PilotSuite Core Add-on connection details."
            },
        )

    async def async_step_reauth(self, user_input: dict | None = None) -> FlowResult:
        return await self.async_step_manual_setup(user_input)

    async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure an existing entry (HA 2024.4+ pattern).

        Called when user clicks "Configure" on an existing integration entry.
        Uses self._get_reconfigure_entry() which auto-sets context["config_entry_id"]
        so subsequent options-flow steps are automatically linked to the entry.
        Accumulates shared parameters (host/port/token/zones) in ConfigFlow._reconfigure_data
        until the user explicitly returns to reconfigure_menu and finishes.
        """
        entry = self._get_reconfigure_entry()
        self._entry = entry

        # Seed shared reconfigure data from current entry — cleared on re-init
        ConfigFlow._reconfigure_data = {}
        base = merge_config_data(entry.data, entry.options)
        for key in (CONF_HOST, CONF_PORT, CONF_TOKEN, CONF_TEST_LIGHT):
            if key in base:
                ConfigFlow._reconfigure_data[key] = base[key]

        return self.async_show_menu(
            step_id="reconfigure_menu",
            menu_options=["reconfigure_connection", "reconfigure_zones", "back"],
            description_placeholders={
                "description": (
                    f"PilotSuite reconfigure — {entry.title}\n\n"
                    "Choose what you want to change:"
                )
            },
        )

    async def async_step_reconfigure_connection(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure connection settings.

        Validates and normalizes host/port/token and stores them in the shared
        ConfigFlow._reconfigure_data dict. Nothing is written to the entry yet —
        that happens only when the user finishes (back → abort with updated data).
        """
        return await self._async_step_reconfigure_connection(user_input, from_options_flow=False)

    async def async_step_reconfigure_zones(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure zones — delegates to OptionsFlowHandler."""
        options_flow = OptionsFlowHandler(self._entry)
        return await options_flow.async_step_habitus_zones(user_input)

    async def async_step_back(self, user_input: dict | None = None) -> FlowResult:
        """Return to reconfigure menu — apply accumulated shared params on exit."""
        pending = ConfigFlow._reconfigure_data
        if pending:
            # Commit accumulated shared params to entry.data exactly once
            updated_data = {**self._entry.data, **pending}
            self.hass.config_entries.async_update_entry(self._entry, data=updated_data)
            ConfigFlow._reconfigure_data = {}
        return self.async_show_menu(
            step_id="reconfigure_menu",
            menu_options=["reconfigure_connection", "reconfigure_zones", "back"],
            description_placeholders={
                "description": (
                    "PilotSuite reconfigure\n\n"
                    "Choose what you want to change:"
                )
            },
        )

    # ── Shared reconfigure helpers ───────────────────────────────────

    async def _async_step_reconfigure_connection(
        self, user_input: dict | None, from_options_flow: bool
    ) -> FlowResult:
        """Shared connection step logic for both ConfigFlow and OptionsFlow reconfigure.

        Args:
            user_input: Form input dict (None = show form).
            from_options_flow: If True, called from OptionsFlowHandler so it owns
                the write-back via _create_merged_entry; ConfigFlow version
                accumulates into _reconfigure_data instead.
        """
        if user_input is not None:
            # Normalize host/port
            base = merge_config_data(self._entry.data, self._entry.options)
            host, port = normalize_host_port(
                user_input.get(CONF_HOST, base.get(CONF_HOST)),
                user_input.get(CONF_PORT, base.get(CONF_PORT)),
            )
            user_input[CONF_HOST] = host
            user_input[CONF_PORT] = port

            # Token handling: support clear / new value / keep existing
            clear_token = user_input.pop("_clear_token", False)
            new_token = user_input.get(CONF_TOKEN, "")
            if clear_token:
                user_input[CONF_TOKEN] = ""
            elif not new_token:
                user_input[CONF_TOKEN] = str(base.get(CONF_TOKEN, "") or "")
            if CONF_TOKEN in user_input:
                user_input[CONF_TOKEN] = user_input[CONF_TOKEN].strip()

            if from_options_flow:
                # OptionsFlow writes immediately via _create_merged_entry
                return None  # caller handles write-back
            else:
                # ConfigFlow: accumulate into shared dict
                for key in (CONF_HOST, CONF_PORT, CONF_TOKEN, CONF_TEST_LIGHT):
                    if key in user_input:
                        ConfigFlow._reconfigure_data[key] = user_input[key]
                return self.async_show_menu(
                    step_id="reconfigure_menu",
                    menu_options=["reconfigure_connection", "reconfigure_zones", "back"],
                    description_placeholders={
                        "description": (
                            "Connection saved. Choose next action or go back to apply."
                        )
                    },
                )

        # Show form with current values (from entry or pending shared data)
        base = merge_config_data(self._entry.data, self._entry.options)
        for key, val in ConfigFlow._reconfigure_data.items():
            base[key] = val

        webhook_id = base.get("webhook_id")
        ha_base = self.hass.config.internal_url or self.hass.config.external_url or ""
        webhook_url = (
            f"{ha_base}/api/webhook/{webhook_id}"
            if webhook_id and ha_base
            else (f"/api/webhook/{webhook_id}" if webhook_id else "(generated after first setup)")
        )
        token_hint = "** SET **" if base.get(CONF_TOKEN) else ""

        from .config_schema_builders import build_connection_schema

        schema = vol.Schema(build_connection_schema(base, webhook_url, token_hint))
        return self.async_show_form(step_id="reconfigure_connection", data_schema=schema)

    # ── Wizard dispatcher ────────────────────────────────────────────

    async def async_step_wizard(self, user_input: dict | None = None) -> FlowResult:
        """Setup wizard - multi-step guided configuration."""
        if not hasattr(self, "_wizard"):
            self._wizard = SetupWizard(self.hass)
            self._data: dict = {}

        wizard = self._wizard
        wizard_step = getattr(self, "_wizard_step", STEP_DISCOVERY)

        # Show form for current step (no user input yet)
        if user_input is None:
            return self._show_wizard_step(wizard_step, wizard)

        # Process input and advance to next step
        if wizard_step == STEP_NETWORK:
            # Network step: validate connectivity on submit.
            allow_offline = bool(user_input.get("allow_offline"))
            network_input = {k: v for k, v in user_input.items() if k != "allow_offline"}

            token = network_input.get(CONF_TOKEN)
            if not isinstance(token, str) or not token.strip():
                step_id, data_schema, desc = build_network_form(hint="Token ist erforderlich.")
                return self.async_show_form(
                    step_id=step_id,
                    data_schema=data_schema,
                    errors={CONF_TOKEN: "required"},
                    description_placeholders=desc,
                )

            try:
                await validate_input(self.hass, network_input)
            except Exception as err:  # noqa: BLE001
                msg = str(err)
                msg_lower = msg.lower()

                # Track consecutive failures for escalation copy.
                fail_count = int(self._data.get("_network_failures", 0)) + 1
                self._data["_network_failures"] = fail_count

                if allow_offline:
                    _LOGGER.warning(
                        "Wizard network step: proceeding despite failed connectivity check (%s)",
                        msg,
                    )
                    self._data["network"] = network_input
                    self._data["_network_offline_override"] = True
                    next_step = STEP_REVIEW
                else:
                    errors: dict[str, str] = {}
                    hint: str | None

                    if "http 401" in msg_lower or "http 403" in msg_lower:
                        errors[CONF_TOKEN] = "invalid_auth"
                        hint = "Authentifizierung fehlgeschlagen. Bitte prüfe Token und Berechtigungen."
                    elif "timeout" in msg_lower or "cannot reach" in msg_lower or "cannot connect" in msg_lower:
                        errors["base"] = "cannot_connect"
                        hint = "Core nicht erreichbar. Prüfe, ob der Dienst läuft."
                    else:
                        errors["base"] = "invalid"
                        hint = "Etwas ist schiefgelaufen. Bitte erneut versuchen."

                    if fail_count >= 3:
                        hint = (
                            hint
                            + "\n\nHinweis: Nach mehreren Fehlversuchen: prüfe Details in den Logs "
                            + "und nutze anschließend Repair (Einstellungen → Geräte & Dienste → PilotSuite)."
                        )

                    step_id, data_schema, desc = build_network_form(hint=hint)
                    return self.async_show_form(
                        step_id=step_id,
                        data_schema=data_schema,
                        errors=errors,
                        description_placeholders=desc,
                    )
            else:
                # Success path
                self._data["network"] = network_input
                self._data.pop("_network_offline_override", None)
                next_step = STEP_REVIEW
        else:
            next_step = self._process_wizard_input(wizard_step, user_input, wizard)

        # Handle async discovery if flagged
        if self._data.pop("_auto_discover", False):
            discovered = await wizard.discover_entities()
            self._data["discovery"] = discovered

        # Final step: create entry
        if next_step is None:
            final_config, title = build_final_config(self._data)
            final_config.setdefault(CONF_ENTITY_PROFILE, DEFAULT_ENTITY_PROFILE)
            try:
                preferred_port = int(final_config.get(CONF_PORT, DEFAULT_PORT))
            except (TypeError, ValueError):
                preferred_port = DEFAULT_PORT
            resolved = await discover_reachable_core_endpoint(
                self.hass,
                preferred_host=str(final_config.get(CONF_HOST, DEFAULT_HOST)),
                preferred_port=preferred_port,
            )
            if resolved is not None:
                final_config[CONF_HOST], final_config[CONF_PORT] = resolved

            # Auto-fetch token if not set (Quick Start / Wizard without manual token)
            if not str(final_config.get(CONF_TOKEN) or "").strip():
                host = str(final_config.get(CONF_HOST, DEFAULT_HOST))
                port = int(final_config.get(CONF_PORT, DEFAULT_PORT))
                final_config[CONF_TOKEN] = await fetch_setup_token(
                    self.hass, host, port
                )

            await self.async_set_unique_id(INTEGRATION_UNIQUE_ID)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=title, data=final_config)

        self._wizard_step = next_step
        return await self.async_step_wizard(None)

    def _show_wizard_step(self, step: str, wizard) -> FlowResult:
        """Show the form for a wizard step."""
        builders = {
            STEP_DISCOVERY: lambda: build_discovery_form(),
            STEP_ZONES: lambda: build_zones_form(wizard),
            STEP_ZONE_ENTITIES: lambda: self._build_zone_entities(wizard),
            STEP_ENTITIES: lambda: build_entities_form(wizard),
            STEP_FEATURES: lambda: build_features_form(),
            STEP_MODULES: lambda: build_modules_form(),
            STEP_NETWORK: lambda: build_network_form(),
            STEP_REVIEW: lambda: build_review_form(self._data),
        }

        step_id, data_schema, desc = builders[step]()
        kwargs: dict = {"step_id": step_id, "data_schema": data_schema}
        if desc:
            kwargs["description_placeholders"] = desc
        return self.async_show_form(**kwargs)

    def _build_zone_entities(self, wizard):
        """Build zone entities form, or skip if no zones selected."""
        selected_zones = self._data.get("selected_zones", [])
        if not selected_zones:
            # No zones selected, skip to entities
            self._wizard_step = STEP_ENTITIES
            return build_entities_form(wizard)
        return build_zone_entities_form(wizard, selected_zones)

    def _process_wizard_input(self, step: str, user_input: dict, wizard) -> str | None:
        """Process wizard step input. Returns next step name or None for final."""
        processors = {
            STEP_DISCOVERY: lambda ui: process_discovery_input(ui, wizard, self._data),
            STEP_ZONES: lambda ui: process_zones_input(ui, self._data),
            STEP_ZONE_ENTITIES: lambda ui: process_zone_entities_input(ui, self._data),
            STEP_ENTITIES: lambda ui: process_entities_input(ui, self._data),
            STEP_FEATURES: lambda ui: process_features_input(ui, self._data),
            STEP_NETWORK: lambda ui: process_network_input(ui, self._data),
            STEP_MODULES: lambda ui: process_modules_input(ui, self._data),
            STEP_REVIEW: lambda ui: None,  # Final step
        }
        return processors[step](user_input)
