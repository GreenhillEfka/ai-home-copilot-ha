"""OptionsFlowHandler for PilotSuite config entry."""
from __future__ import annotations

import json
import logging

import voluptuous as vol
import yaml

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .config_helpers import merge_config_data, parse_csv


def _compute_delta(existing: dict, new_partial: dict) -> dict:
    """Return only the keys in new_partial that differ from existing.

    Compares values deeply for list/dict, identity for everything else.
    Keys present in new_partial with the same value as in existing are
    excluded — only actual deltas are written back to the config entry.
    This prevents unrelated keys from being overwritten when a user changes
    only one setting in a multi-step options flow.
    """
    delta: dict[str, object] = {}
    for key, new_val in new_partial.items():
        old_val = existing.get(key)
        if old_val is None and new_val is None:
            continue
        # Deep-compare lists and dicts; identity compare for primitives.
        if isinstance(new_val, list) and isinstance(old_val, list):
            if new_val != old_val:
                delta[key] = new_val
        elif isinstance(new_val, dict) and isinstance(old_val, dict):
            if new_val != old_val:
                delta[key] = new_val
        elif new_val != old_val:
            delta[key] = new_val
    return delta
from .core_endpoint import normalize_host_port
from .config_schema_builders import (
    build_neuron_schema,
    build_llm_provider_schema,
    build_knowledge_graph_schema,
    build_autonomy_schema,
    build_zone_health_schema,
    build_anomaly_habitus_schema,
)
from .config_snapshot_flow import ConfigSnapshotOptionsFlow
from .config_zones_flow import async_step_zone_form, async_sync_zone_editor_zone
from .config_tags_flow import async_step_add_tag, async_step_edit_tag, async_step_delete_tag
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    CONF_TEST_LIGHT,
    CONF_WEBHOOK_URL,
    CONF_MEDIA_MUSIC_PLAYERS,
    CONF_MEDIA_TV_PLAYERS,
    CONF_SUGGESTION_SEED_ENTITIES,
    CONF_EVENTS_FORWARDER_ADDITIONAL_ENTITIES,
    CONF_TRACKED_USERS,
    CONF_NEURON_CONTEXT_ENTITIES,
    CONF_NEURON_STATE_ENTITIES,
    CONF_NEURON_MOOD_ENTITIES,
    CONF_WASTE_ENTITIES,
    CONF_BIRTHDAY_CALENDAR_ENTITIES,
    CONF_PRIMARY_USER,
    CONF_WASTE_TTS_ENTITY,
    CONF_BIRTHDAY_TTS_ENTITY,
    CONF_LLM_PREFER_LOCAL,
    CONF_LLM_CLOUD_API_URL,
    CONF_LLM_CLOUD_API_KEY,
    CONF_LLM_CLOUD_MODEL,
    CONF_LLM_OLLAMA_MODEL,
    CONF_ML_ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_entity_list(value: object) -> list[str]:
    """Normalize selector/csv values into list[str]."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return parse_csv(value)
    if value is None:
        return []
    item = str(value).strip()
    return [item] if item else []


class OptionsFlowHandler(config_entries.OptionsFlow, ConfigSnapshotOptionsFlow):
    # ── Shared reconfigure parameter staging ────────────────────────
    # Accumulates connection params (host/port/token/test_light) during reconfigure
    # flow. Written exactly once — on back navigation back to the reconfigure menu —
    # to avoid discarding changes when the user switches between steps.
    _pending_shared_params: dict = {}

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._entry = config_entry
        self._config_entry_id = config_entry.entry_id
        ConfigSnapshotOptionsFlow.__init__(self, config_entry)

    def _get_config_entry(self):
        entry = getattr(self, "config_entry", None) or getattr(self, "_entry", None)
        if entry is None:
            msg = "OptionsFlowHandler has no config entry bound"
            raise AttributeError(msg)
        return entry

    def _effective_config(self) -> dict:
        """Return merged live config (entry.data + entry.options)."""
        entry = self._get_config_entry()
        return merge_config_data(entry.data, entry.options)

    def _create_merged_entry(self, updates: dict) -> FlowResult:
        """Write only the delta between the current config entry state and the submitted form data.

        Uses ``self.config_entry.data`` as the authoritative baseline (the last committed state),
        diffs it against ``updates``, and passes only changed keys to the options layer.
        This prevents form re-submissions from overwriting keys that exist in
        ``entry.data`` but were not touched in the current step.
        """
        # entry.data is the stable baseline; entry.options may carry in-flight state.
        # We always diff from entry.data so that options-flow re-navigation does not
        # corrupt keys that belong to other steps.
        entry = self._get_config_entry()
        current = dict(entry.data)
        delta = _compute_delta(current, updates)
        if delta:
            _LOGGER.debug("Delta-write: writing %d changed key(s): %s", len(delta), list(delta.keys()))
        return self.async_create_entry(title="", data=delta)

    def _flush_pending_shared_params(self) -> None:
        """Write accumulated shared params to entry.data exactly once (on back/exit).

        This is called from async_step_back when returning to the reconfigure menu,
        ensuring that any edits made in the connection step are preserved even if
        the user subsequently visits other steps (e.g. zones) before finishing.
        """
        pending = OptionsFlowHandler._pending_shared_params
        if not pending:
            return
        # Write to entry.data so the values survive across OptionsFlowHandler
        # re-instantiation when the user re-enters the connection step
        entry = self._get_config_entry()
        updated_data = {**entry.data, **pending}
        self.hass.config_entries.async_update_entry(entry, data=updated_data)
        # Clear staging — write happened exactly once
        OptionsFlowHandler._pending_shared_params = {}

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["connection", "modules", "llm_provider", "knowledge_graph", "autonomy", "zone_health", "ml_anomaly", "automation_modes", "habitus_zones", "entity_tags", "neurons"],
        )

    # ── Connection ───────────────────────────────────────────────────

    async def async_step_connection(self, user_input: dict | None = None) -> FlowResult:
        """Network settings: host, port, token, webhook URL, test light."""
        if user_input is not None:
            user_input.pop(CONF_WEBHOOK_URL, None)
            data = self._effective_config()
            host, port = normalize_host_port(
                user_input.get(CONF_HOST, data.get(CONF_HOST)),
                user_input.get(CONF_PORT, data.get(CONF_PORT)),
            )
            user_input[CONF_HOST] = host
            user_input[CONF_PORT] = port

            clear_token = user_input.pop("_clear_token", False)
            new_token = user_input.get(CONF_TOKEN, "")

            if clear_token:
                user_input[CONF_TOKEN] = ""
            elif not new_token:
                existing_token = str(data.get(CONF_TOKEN, "") or "")
                user_input[CONF_TOKEN] = existing_token

            if CONF_TOKEN in user_input:
                token = user_input.get(CONF_TOKEN, "").strip()
                if not token:
                    user_input[CONF_TOKEN] = ""

            # Optional selector: keep prior value when UI submits null.
            test_light = user_input.get(CONF_TEST_LIGHT)
            if test_light in (None, ""):
                existing_test_light = str(data.get(CONF_TEST_LIGHT) or "").strip()
                if existing_test_light:
                    user_input[CONF_TEST_LIGHT] = existing_test_light
                else:
                    user_input.pop(CONF_TEST_LIGHT, None)

            return self._create_merged_entry(user_input)

        data = self._effective_config()

        webhook_id = data.get("webhook_id")
        base = self.hass.config.internal_url or self.hass.config.external_url or ""
        webhook_url = (
            f"{base}/api/webhook/{webhook_id}"
            if webhook_id and base
            else (f"/api/webhook/{webhook_id}" if webhook_id else "(generated after first setup)")
        )

        current_token = data.get(CONF_TOKEN, "")
        token_hint = "** SET **" if current_token else ""

        from .config_schema_builders import build_connection_schema
        schema = vol.Schema(build_connection_schema(data, webhook_url, token_hint))
        return self.async_show_form(step_id="connection", data_schema=schema)

    # ── Reconfigure (HA 2024.4+ entry point) ─────────────────────────

    async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure entry menu (HA 2024.4+ pattern).

        Called from ConfigFlow.async_step_reconfigure via options-flow delegation.
        self._entry is already set by ConfigFlow before calling.
        """
        return self.async_show_menu(
            step_id="reconfigure_menu",
            menu_options=["reconfigure_connection", "reconfigure_zones", "reconfigure_back"],
            description_placeholders={
                "description": (
                    f"PilotSuite reconfigure — {getattr(self._entry, 'title', 'PilotSuite')}\n\n"
                    "Choose what you want to change:"
                )
            },
        )

    async def async_step_reconfigure_connection(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure connection settings.

        Connection edits are staged in _pending_shared_params and flushed to
        entry.data on back navigation — never discarded by re-entering the
        step or switching to another reconfigure sub-step.
        """
        return await self._async_step_reconfigure_connection(user_input, from_options_flow=True)

    async def async_step_reconfigure_zones(self, user_input: dict | None = None) -> FlowResult:
        """Reconfigure zones."""
        return await self.async_step_habitus_zones(user_input)

    async def async_step_reconfigure_back(self, user_input: dict | None = None) -> FlowResult:
        """Return to reconfigure menu — flush pending shared params on exit."""
        self._flush_pending_shared_params()
        return self.async_show_menu(
            step_id="reconfigure_menu",
            menu_options=["reconfigure_connection", "reconfigure_zones", "reconfigure_back"],
            description_placeholders={
                "description": (
                    "PilotSuite reconfigure\n\n"
                    "Choose what you want to change:"
                )
            },
        )

    # ── Shared connection step logic ─────────────────────────────────

    async def _async_step_reconfigure_connection(
        self, user_input: dict | None, from_options_flow: bool
    ) -> FlowResult:
        """Shared connection step logic for both ConfigFlow and OptionsFlow reconfigure.

        Args:
            user_input: Form input dict (None = show form).
            from_options_flow: If True, called from OptionsFlowHandler — stages
                writes in _pending_shared_params instead of committing immediately.
        """
        if user_input is not None:
            # Normalize host/port
            base = self._effective_config()
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
                # Stage shared params for flush on back navigation
                for key in (CONF_HOST, CONF_PORT, CONF_TOKEN, CONF_TEST_LIGHT):
                    if key in user_input:
                        OptionsFlowHandler._pending_shared_params[key] = user_input[key]
                # Also write via _create_merged_entry so other steps see the update
                # immediately (non-shared fields go to options, shared go to data
                # via _flush_pending_shared_params on back)
                non_shared = {k: v for k, v in user_input.items()
                              if k not in (CONF_HOST, CONF_PORT, CONF_TOKEN)}
                return self._create_merged_entry(non_shared)
            else:
                # ConfigFlow path — accumulate into class-level dict
                for key in (CONF_HOST, CONF_PORT, CONF_TOKEN, CONF_TEST_LIGHT):
                    if key in user_input:
                        OptionsFlowHandler._pending_shared_params[key] = user_input[key]
                return self.async_show_menu(
                    step_id="reconfigure_menu",
                    menu_options=["reconfigure_connection", "reconfigure_zones", "back"],
                    description_placeholders={
                        "description": "Connection saved. Choose next action or go back to apply."
                    },
                )

        # Show form with current values (effective config)
        base = self._effective_config()
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

    # ── Modules ──────────────────────────────────────────────────────

    async def async_step_modules(self, user_input: dict | None = None) -> FlowResult:
        """Module toggles and settings."""
        if user_input is not None:
            # Normalize entity-selection fields (selectors + backward-compatible csv).
            for field in (
                CONF_SUGGESTION_SEED_ENTITIES,
                CONF_MEDIA_MUSIC_PLAYERS,
                CONF_MEDIA_TV_PLAYERS,
                CONF_EVENTS_FORWARDER_ADDITIONAL_ENTITIES,
                CONF_TRACKED_USERS,
                CONF_WASTE_ENTITIES,
                CONF_BIRTHDAY_CALENDAR_ENTITIES,
                CONF_ML_ENTITIES,
            ):
                if field in user_input:
                    user_input[field] = _normalize_entity_list(user_input.get(field))

            # Normalize optional single-entity selectors.
            for field in (CONF_PRIMARY_USER, CONF_WASTE_TTS_ENTITY, CONF_BIRTHDAY_TTS_ENTITY):
                if field in user_input and user_input[field] is None:
                    user_input[field] = ""

            return self._create_merged_entry(user_input)

        data = self._effective_config()
        from .config_schema_builders import build_modules_schema
        schema = vol.Schema(build_modules_schema(data))
        return self.async_show_form(step_id="modules", data_schema=schema)

    # ── LLM Provider / OpenClaw ─────────────────────────────────────

    async def async_step_llm_provider(self, user_input: dict | None = None) -> FlowResult:
        """Configure LLM provider: local Ollama vs. Cloud/OpenClaw endpoint."""
        if user_input is not None:
            # Strip whitespace from text fields
            for field in (CONF_LLM_CLOUD_API_URL, CONF_LLM_CLOUD_API_KEY, CONF_LLM_CLOUD_MODEL, CONF_LLM_OLLAMA_MODEL):
                if field in user_input and isinstance(user_input[field], str):
                    user_input[field] = user_input[field].strip()

            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_llm_provider_schema(data))
        return self.async_show_form(
            step_id="llm_provider",
            data_schema=schema,
            description_placeholders={
                "description": (
                    "Configure the LLM backend for PilotSuite Core.\n\n"
                    "**Local (Ollama):** Runs on-device via the Core add-on (default, privacy-first).\n\n"
                    "**Cloud / OpenClaw:** Any OpenAI-compatible endpoint "
                    "(e.g. http://openclaw.local:8080/v1). Requires API key and model name.\n\n"
                    "When 'Prefer local model' is enabled, Ollama is used whenever available "
                    "and Cloud is only used as fallback."
                )
            },
        )

    # ── Habitus zones ────────────────────────────────────────────────

    async def async_step_habitus_zones(self, user_input: dict | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="habitus_zones",
            menu_options=[
                "create_zone",
                "edit_zone",
                "delete_zone",
                "generate_dashboard",
                "publish_dashboard",
                "bulk_edit",
                "back",
            ],
        )

    async def async_step_back(self, user_input: dict | None = None) -> FlowResult:
        """Return to the appropriate parent menu.

        If this flow was entered via ConfigFlow.async_step_reconfigure (HA 2024.4+),
        self.context["reconfigure"] is True — return to the reconfigure menu.
        Flushes pending shared params to entry.data before navigating away
        so edits survive re-entering the connection step.
        """
        self._flush_pending_shared_params()
        if self.context.get("reconfigure"):
            return self.async_show_menu(
                step_id="reconfigure_menu",
                menu_options=["reconfigure_connection", "reconfigure_zones", "reconfigure_back"],
                description_placeholders={
                    "description": (
                        "PilotSuite reconfigure\n\n"
                        "Choose what you want to change:"
                    )
                },
            )
        return await self.async_step_init()

    # ── Entity Tags ─────────────────────────────────────────────────

    async def async_step_entity_tags(self, user_input: dict | None = None) -> FlowResult:
        """Show entity tags management menu."""
        return self.async_show_menu(
            step_id="entity_tags",
            menu_options=["add_tag", "edit_tag", "delete_tag", "back"],
        )

    async def async_step_add_tag(self, user_input: dict | None = None) -> FlowResult:
        return await async_step_add_tag(self, user_input)

    async def async_step_edit_tag(self, user_input: dict | None = None) -> FlowResult:
        return await async_step_edit_tag(self, user_input)

    async def async_step_delete_tag(self, user_input: dict | None = None) -> FlowResult:
        return await async_step_delete_tag(self, user_input)

    async def async_step_create_zone(self, user_input: dict | None = None) -> FlowResult:
        return await async_step_zone_form(self, mode="create", user_input=user_input)

    async def async_step_edit_zone(self, user_input: dict | None = None) -> FlowResult:
        from .habitus_zones_store_v2 import async_get_zones_v2

        zones = await async_get_zones_v2(self.hass, self._config_entry_id)
        if not zones:
            return self.async_abort(reason="no_zones")

        if user_input is None:
            options = [
                selector.SelectOptionDict(value=z.zone_id, label=f"{z.name} ({z.zone_id})")
                for z in zones
            ]
            schema = vol.Schema(
                {
                    vol.Required("zone_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            )
            return self.async_show_form(step_id="edit_zone", data_schema=schema)

        zid = str(user_input.get("zone_id", ""))
        return await async_step_zone_form(self, mode="edit", user_input=None, zone_id=zid)

    async def async_step_delete_zone(self, user_input: dict | None = None) -> FlowResult:
        from .habitus_zones_store_v2 import async_get_zones_v2, async_set_zones_v2

        zones = await async_get_zones_v2(self.hass, self._config_entry_id)
        if not zones:
            return self.async_abort(reason="no_zones")

        if user_input is None:
            options = [
                selector.SelectOptionDict(value=z.zone_id, label=f"{z.name} ({z.zone_id})")
                for z in zones
            ]
            schema = vol.Schema(
                {
                    vol.Required("zone_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            )
            return self.async_show_form(step_id="delete_zone", data_schema=schema)

        zid = str(user_input.get("zone_id", ""))
        remain = [z for z in zones if z.zone_id != zid]
        await async_set_zones_v2(self.hass, self._config_entry_id, remain)

        synced = await async_sync_zone_editor_zone(
            self,
            mode="delete",
            zone=None,
            previous_zone_id=zid,
        )
        if not synced:
            _LOGGER.debug("Core zone-editor sync not confirmed for deleted zone: %s", zid)

        return await self.async_step_habitus_zones()

    async def async_step_bulk_edit(self, user_input: dict | None = None) -> FlowResult:
        """Bulk editor to paste YAML/JSON (no 255-char limit) with validation."""
        from .habitus_zones_store_v2 import async_get_zones_v2, async_set_zones_v2_from_raw

        zones = await async_get_zones_v2(self.hass, self._config_entry_id)
        current = []
        for z in zones:
            item = {"id": z.zone_id, "name": z.name}
            if isinstance(getattr(z, "entities", None), dict) and z.entities:
                item["entities"] = z.entities
            else:
                item["entity_ids"] = z.entity_ids
            current.append(item)

        if user_input is not None:
            raw_text = str(user_input.get("zones") or "").strip()
            if not raw_text:
                raw_text = "[]"

            try:
                try:
                    raw = json.loads(raw_text)
                except Exception:  # noqa: BLE001
                    raw = yaml.safe_load(raw_text)

                await async_set_zones_v2_from_raw(self.hass, self._config_entry_id, raw)
            except Exception as err:  # noqa: BLE001
                return self.async_show_form(
                    step_id="bulk_edit",
                    data_schema=vol.Schema(
                        {
                            vol.Required("zones", default=raw_text): selector.TextSelector(
                                selector.TextSelectorConfig(multiline=True)
                            )
                        }
                    ),
                    errors={"base": "invalid_json"},
                    description_placeholders={"hint": f"Parse/validation error: {err}"},
                )

            return await self.async_step_habitus_zones()

        default = yaml.safe_dump(current, allow_unicode=True, sort_keys=False)
        schema = vol.Schema(
            {
                vol.Required("zones", default=default): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                )
            }
        )

        return self.async_show_form(
            step_id="bulk_edit",
            data_schema=schema,
            description_placeholders={
                "hint": (
                    "Paste a YAML/JSON list of zones (or {zones:[...]}). Each zone requires at least one valid entity_id.\n\n"
                    "Optional: use a categorized structure via `entities:` (role -> list of entity_ids), e.g.\n"
                    "- entities: {motion: [...], lights: [...], brightness: [...], heating: [...], humidity: [...], co2: [...], cover: [...], door: [...], window: [...], lock: [...], media: [...], other: [...]}"
                ),
            },
        )

    # ── Dashboard generation ─────────────────────────────────────────

    async def async_step_generate_dashboard(self, user_input: dict | None = None) -> FlowResult:
        """Generate Lovelace dashboard YAML for all Habitus zones."""
        from .habitus_dashboard import async_generate_habitus_zones_dashboard

        if user_input is not None:
            try:
                path = await async_generate_habitus_zones_dashboard(self.hass, self._config_entry_id)
                return self.async_abort(
                    reason="dashboard_generated",
                    description_placeholders={"path": str(path)},
                )
            except Exception as err:  # noqa: BLE001
                return self.async_show_form(
                    step_id="generate_dashboard",
                    errors={"base": "generation_failed"},
                    description_placeholders={"error": str(err)},
                )

        schema = vol.Schema({vol.Optional("confirm", default=True): bool})
        return self.async_show_form(
            step_id="generate_dashboard",
            data_schema=schema,
            description_placeholders={
                "description": (
                    "Creates a Lovelace YAML dashboard file for all Habitus zones. "
                    "The file is saved in the `pilotsuite-styx/` configuration folder "
                    "(with legacy mirror in `copilot_ha/`)."
                )
            },
        )

    async def async_step_publish_dashboard(self, user_input: dict | None = None) -> FlowResult:
        """Publish the latest generated dashboard to www folder."""
        from .habitus_dashboard import async_publish_last_habitus_dashboard

        if user_input is not None:
            try:
                url = await async_publish_last_habitus_dashboard(self.hass)
                return self.async_abort(
                    reason="dashboard_published",
                    description_placeholders={"url": url},
                )
            except FileNotFoundError:
                return self.async_show_form(
                    step_id="publish_dashboard",
                    errors={"base": "no_dashboard_generated"},
                    description_placeholders={
                        "hint": "Generate a dashboard first using 'Generate dashboard YAML'."
                    },
                )
            except Exception as err:  # noqa: BLE001
                return self.async_show_form(
                    step_id="publish_dashboard",
                    errors={"base": "publish_failed"},
                    description_placeholders={"error": str(err)},
                )

        schema = vol.Schema({vol.Optional("confirm", default=True): bool})
        return self.async_show_form(
            step_id="publish_dashboard",
            data_schema=schema,
            description_placeholders={
                "description": (
                    "Copies the latest generated dashboard to `www/pilotsuite-styx/` "
                    "(plus legacy mirror in `www/copilot_ha/`) for easy download."
                )
            },
        )

    # ── Automation Modes ──────────────────────────────────────────────

    async def async_step_automation_modes(self, user_input: dict | None = None) -> FlowResult:
        """Configure automation mode (off / learning / autonomy) per zone.

        Each zone can operate in one of three modes:
        - off:       Sensors report but no automations fire
        - learning:  Sensors report + pattern recording, no actions
        - autonomy:  Full automation (lights, music, suggestions)
        """
        from .habitus_zones_store_v2 import async_get_zones_v2

        zones = await async_get_zones_v2(self.hass, self._config_entry_id)
        data = self._effective_config()

        # Load existing mode config
        zone_modes: dict = data.get("zone_automation_modes", {})
        global_mode: str = data.get("global_automation_mode", "learning")

        if user_input is not None:
            new_global = user_input.get("global_mode", global_mode)
            updates = {
                "global_automation_mode": new_global,
                "zone_automation_modes": {},
            }

            for z in zones:
                key = f"mode_{z.zone_id}"
                mode = user_input.get(key, new_global)
                if mode in ("off", "learning", "autonomy"):
                    updates["zone_automation_modes"][z.zone_id] = mode

            return self._create_merged_entry(updates)

        mode_options = [
            selector.SelectOptionDict(value="off", label="Aus (off)"),
            selector.SelectOptionDict(value="learning", label="Lernen (learning)"),
            selector.SelectOptionDict(value="autonomy", label="Autonomie (autonomy)"),
        ]

        schema_fields: dict = {
            vol.Required("global_mode", default=global_mode): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=mode_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }

        for z in zones:
            zone_mode = zone_modes.get(z.zone_id, global_mode)
            schema_fields[vol.Required(f"mode_{z.zone_id}", default=zone_mode)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=mode_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )

        schema = vol.Schema(schema_fields)
        descriptions = {
            "description": (
                "Steuere den Automationsmodus pro Zone:\n"
                "- **Aus**: Sensoren melden, aber keine Aktionen\n"
                "- **Lernen**: Sensoren + Mustererkennung, keine Aktionen\n"
                "- **Autonomie**: Volle Automatisierung (Licht, Musik, Vorschlaege)"
            )
        }
        return self.async_show_form(
            step_id="automation_modes",
            data_schema=schema,
            description_placeholders=descriptions,
        )

    # ── Neurons ──────────────────────────────────────────────────────

    async def async_step_neurons(self, user_input: dict | None = None) -> FlowResult:
        """Configure neural system entities."""
        if user_input is not None:
            for field in (CONF_NEURON_CONTEXT_ENTITIES, CONF_NEURON_STATE_ENTITIES, CONF_NEURON_MOOD_ENTITIES):
                if field in user_input:
                    user_input[field] = _normalize_entity_list(user_input.get(field))

            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_neuron_schema(data))
        return self.async_show_form(step_id="neurons", data_schema=schema)

    # ── Knowledge Graph ───────────────────────────────────────────────

    async def async_step_knowledge_graph(self, user_input: dict | None = None) -> FlowResult:
        """Configure knowledge graph sync settings."""
        if user_input is not None:
            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_knowledge_graph_schema(data))
        return self.async_show_form(step_id="knowledge_graph", data_schema=schema)

    # ── Autonomy ──────────────────────────────────────────────────────

    async def async_step_autonomy(self, user_input: dict | None = None) -> FlowResult:
        """Configure autonomy system settings."""
        if user_input is not None:
            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_autonomy_schema(data))
        return self.async_show_form(step_id="autonomy", data_schema=schema)

    # ── Zone Health ───────────────────────────────────────────────────

    async def async_step_zone_health(self, user_input: dict | None = None) -> FlowResult:
        """Configure zone health polling settings."""
        if user_input is not None:
            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_zone_health_schema(data))
        return self.async_show_form(step_id="zone_health", data_schema=schema)

    # ── ML / Anomaly ──────────────────────────────────────────────────

    async def async_step_ml_anomaly(self, user_input: dict | None = None) -> FlowResult:
        """Configure ML context, anomaly detection, and habitus mining."""
        if user_input is not None:
            if CONF_ML_ENTITIES in user_input:
                user_input[CONF_ML_ENTITIES] = _normalize_entity_list(user_input.get(CONF_ML_ENTITIES))

            return self._create_merged_entry(user_input)

        data = self._effective_config()
        schema = vol.Schema(build_anomaly_habitus_schema(data))
        return self.async_show_form(step_id="ml_anomaly", data_schema=schema)
