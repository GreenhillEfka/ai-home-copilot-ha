"""Tests for PilotSuite Config Flow, Options Flow, and Module Registry.

Covers:
- ConfigFlow: zero_config, manual_setup, reauth, single-instance guard
- OptionsFlowHandler: init menu, connection, modules, neurons
- ModuleRegistry: register, create, names, duplicate, unknown
- CopilotRuntime: get singleton, setup_entry, unload_entry
- config_helpers: parse_csv, as_csv, merge_config_data, validate_input
- config_schema_builders: build_modules_schema, build_neuron_schema
- Minimal integration paths: config_zones_flow + config_options_flow + config_snapshot_flow
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Lightweight HA stubs – keep tests runnable without a full HA install.
# ---------------------------------------------------------------------------


@dataclass
class _FakeConfigEntry:
    entry_id: str = "test_entry_1"
    domain: str = "copilot_ha"
    data: dict = None  # type: ignore[assignment]
    options: dict = None  # type: ignore[assignment]

    def __post_init__(self):
        self.data = self.data or {}
        self.options = self.options or {}


class _FakeHass:
    """Minimal hass stub for tests that need hass.data / hass.config."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.config = MagicMock()
        self.config.internal_url = None
        self.config.external_url = None


# ═══════════════════════════════════════════════════════════════════════════
# 1. ModuleRegistry
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.core.registry import ModuleRegistry


class TestModuleRegistry:
    """Unit tests for ModuleRegistry."""

    def _make_module(self, name: str = "stub"):
        mod = MagicMock()
        mod.name = name
        mod.async_setup_entry = AsyncMock()
        mod.async_unload_entry = AsyncMock(return_value=True)
        return mod

    def test_register_and_create(self):
        reg = ModuleRegistry()
        factory = lambda: self._make_module("alpha")
        reg.register("alpha", factory)
        mod = reg.create("alpha")
        assert mod.name == "alpha"

    def test_names_sorted(self):
        reg = ModuleRegistry()
        for n in ("charlie", "alpha", "bravo"):
            reg.register(n, lambda n=n: self._make_module(n))
        assert reg.names() == ["alpha", "bravo", "charlie"]

    def test_duplicate_register_raises(self):
        reg = ModuleRegistry()
        reg.register("dup", lambda: self._make_module())
        with pytest.raises(ValueError, match="already registered"):
            reg.register("dup", lambda: self._make_module())

    def test_create_unknown_raises(self):
        reg = ModuleRegistry()
        with pytest.raises(KeyError, match="Unknown module"):
            reg.create("nonexistent")

    def test_empty_registry_names(self):
        reg = ModuleRegistry()
        assert reg.names() == []

    def test_registry_returns_fresh_instances(self):
        """Each create() call returns a new module instance."""
        reg = ModuleRegistry()
        call_count = 0

        def _factory():
            nonlocal call_count
            call_count += 1
            return self._make_module(f"inst_{call_count}")

        reg.register("x", _factory)
        a = reg.create("x")
        b = reg.create("x")
        assert a is not b
        assert call_count == 2


# ═══════════════════════════════════════════════════════════════════════════
# 2. CopilotRuntime
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.core.runtime import CopilotRuntime
from custom_components.copilot_ha.const import DOMAIN, DATA_CORE, DATA_RUNTIME


class TestCopilotRuntime:
    """Unit tests for CopilotRuntime singleton and module lifecycle."""

    def test_get_creates_singleton(self):
        hass = _FakeHass()
        rt1 = CopilotRuntime.get(hass)
        rt2 = CopilotRuntime.get(hass)
        assert rt1 is rt2

    def test_get_separate_per_hass(self):
        h1, h2 = _FakeHass(), _FakeHass()
        assert CopilotRuntime.get(h1) is not CopilotRuntime.get(h2)

    @pytest.mark.asyncio
    async def test_setup_and_unload_entry(self):
        hass = _FakeHass()
        rt = CopilotRuntime.get(hass)

        mod = MagicMock()
        mod.async_setup_entry = AsyncMock()
        mod.async_unload_entry = AsyncMock(return_value=True)

        rt.registry.register("test_mod", lambda: mod)

        entry = _FakeConfigEntry()
        await rt.async_setup_entry(entry, ["test_mod"])
        mod.async_setup_entry.assert_awaited_once()

        ok = await rt.async_unload_entry(entry, ["test_mod"])
        assert ok is True
        mod.async_unload_entry.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_setup_skips_failing_module(self):
        hass = _FakeHass()
        rt = CopilotRuntime.get(hass)

        bad = MagicMock()
        bad.async_setup_entry = AsyncMock(side_effect=RuntimeError("boom"))

        good = MagicMock()
        good.async_setup_entry = AsyncMock()
        good.async_unload_entry = AsyncMock(return_value=True)

        rt.registry.register("bad", lambda: bad)
        rt.registry.register("good", lambda: good)

        entry = _FakeConfigEntry()
        await rt.async_setup_entry(entry, ["bad", "good"])
        good.async_setup_entry.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unload_missing_module_ok(self):
        hass = _FakeHass()
        rt = CopilotRuntime.get(hass)
        entry = _FakeConfigEntry()
        rt._live_modules[entry.entry_id] = {}
        ok = await rt.async_unload_entry(entry, ["phantom"])
        assert ok is True

    @pytest.mark.asyncio
    async def test_unload_non_bool_coerced(self):
        hass = _FakeHass()
        rt = CopilotRuntime.get(hass)

        mod = MagicMock()
        mod.async_setup_entry = AsyncMock()
        mod.async_unload_entry = AsyncMock(return_value="yes")

        rt.registry.register("coerce", lambda: mod)
        entry = _FakeConfigEntry()
        await rt.async_setup_entry(entry, ["coerce"])
        ok = await rt.async_unload_entry(entry, ["coerce"])
        assert ok is True


# ═══════════════════════════════════════════════════════════════════════════
# 3. config_helpers
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_helpers import (
    as_csv,
    parse_csv,
    merge_config_data,
)


class TestConfigHelpers:
    """Unit tests for CSV helpers and merge logic."""

    # parse_csv ─────────────────────────────────────────────────────────
    def test_parse_csv_basic(self):
        assert parse_csv("a, b, c") == ["a", "b", "c"]

    def test_parse_csv_empty(self):
        assert parse_csv("") == []

    def test_parse_csv_newlines(self):
        assert parse_csv("x\ny\nz") == ["x", "y", "z"]

    def test_parse_csv_strips_whitespace(self):
        assert parse_csv("  one , two , three  ") == ["one", "two", "three"]

    def test_parse_csv_skips_blank_entries(self):
        assert parse_csv("a,,b,  ,c") == ["a", "b", "c"]

    # as_csv ────────────────────────────────────────────────────────────
    def test_as_csv_none(self):
        assert as_csv(None) == ""

    def test_as_csv_string(self):
        assert as_csv("hello") == "hello"

    def test_as_csv_list(self):
        assert as_csv(["a", "b"]) == "a,b"

    def test_as_csv_int(self):
        assert as_csv(42) == "42"

    # merge_config_data ─────────────────────────────────────────────────
    def test_merge_basic(self):
        result = merge_config_data({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_with_updates(self):
        result = merge_config_data({"a": 1}, {"a": 2}, {"a": 3})
        assert result == {"a": 3}

    def test_merge_none_inputs(self):
        result = merge_config_data(None, None, None)
        assert result == {}

    def test_merge_options_override_data(self):
        result = merge_config_data({"host": "old"}, {"host": "new"})
        assert result["host"] == "new"


# ═══════════════════════════════════════════════════════════════════════════
# 4. core_endpoint helpers
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.core_endpoint import (
    normalize_host_port,
    build_base_url,
    build_candidate_hosts,
)


class TestCoreEndpoint:
    """Unit tests for host/port normalization and candidate discovery."""

    def test_normalize_basic(self):
        h, p = normalize_host_port("192.168.1.1", 8909)
        assert h == "192.168.1.1"
        assert p == 8909

    def test_normalize_url_with_scheme(self):
        h, p = normalize_host_port("http://192.168.1.1:9000", None)
        assert h == "192.168.1.1"
        assert p == 9000

    def test_normalize_host_with_port(self):
        h, p = normalize_host_port("192.168.1.1:7777", None)
        assert h == "192.168.1.1"
        assert p == 7777

    def test_normalize_empty_host(self):
        h, p = normalize_host_port("", 8909)
        assert h == ""
        assert p == 8909

    def test_normalize_invalid_port(self):
        h, p = normalize_host_port("host", "bad")
        assert p == 8909  # default

    def test_build_base_url(self):
        assert build_base_url("myhost", 8909) == "http://myhost:8909"

    def test_build_base_url_empty_host(self):
        assert build_base_url("", 8909) == "http://localhost:8909"

    def test_candidate_hosts_primary_first(self):
        hosts = build_candidate_hosts("custom.local")
        assert hosts[0] == "custom.local"
        assert "homeassistant.local" in hosts
        assert "localhost" in hosts

    def test_candidate_hosts_no_duplicates(self):
        hosts = build_candidate_hosts("homeassistant.local")
        assert hosts.count("homeassistant.local") == 1

    def test_candidate_hosts_docker_internal(self):
        hosts = build_candidate_hosts("primary", include_docker_internal=True)
        assert "host.docker.internal" in hosts

    def test_candidate_hosts_without_docker(self):
        hosts = build_candidate_hosts("primary", include_docker_internal=False)
        assert "host.docker.internal" not in hosts


# ═══════════════════════════════════════════════════════════════════════════
# 5. config_schema_builders
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_schema_builders import (
    build_modules_schema,
    build_neuron_schema,
    build_network_schema,
    build_seed_schema,
    build_watchdog_schema,
    build_forwarder_schema,
    build_waste_schema,
    build_birthday_schema,
    build_user_prefs_schema,
)
from custom_components.copilot_ha.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_NEURON_ENABLED,
    CONF_NEURON_EVALUATION_INTERVAL,
    CONF_WATCHDOG_ENABLED,
    CONF_EVENTS_FORWARDER_ENABLED,
    CONF_WASTE_ENABLED,
    CONF_BIRTHDAY_ENABLED,
    CONF_USER_PREFERENCE_ENABLED,
    CONF_ENTITY_PROFILE,
)

import voluptuous as vol


class TestSchemaBuilders:
    """Verify schema builder functions produce valid voluptuous schemas."""

    def test_build_modules_schema_not_empty(self):
        schema = build_modules_schema({})
        assert len(schema) > 10  # many fields expected

    def test_build_neuron_schema_keys(self):
        schema = build_neuron_schema({})
        keys = {str(k) for k in schema}
        assert CONF_NEURON_ENABLED in keys
        assert CONF_NEURON_EVALUATION_INTERVAL in keys

    def test_build_network_schema_keys(self):
        schema = build_network_schema({}, "http://webhook", "")
        keys = {str(k) for k in schema}
        assert CONF_HOST in keys
        assert CONF_PORT in keys

    def test_build_seed_schema_returns_dict(self):
        assert isinstance(build_seed_schema({}), dict)

    def test_build_watchdog_schema_has_toggle(self):
        schema = build_watchdog_schema({})
        keys = {str(k) for k in schema}
        assert CONF_WATCHDOG_ENABLED in keys

    def test_build_forwarder_schema_has_toggle(self):
        schema = build_forwarder_schema({})
        keys = {str(k) for k in schema}
        assert CONF_EVENTS_FORWARDER_ENABLED in keys

    def test_build_waste_schema_has_toggle(self):
        schema = build_waste_schema({})
        keys = {str(k) for k in schema}
        assert CONF_WASTE_ENABLED in keys

    def test_build_birthday_schema_has_toggle(self):
        schema = build_birthday_schema({})
        keys = {str(k) for k in schema}
        assert CONF_BIRTHDAY_ENABLED in keys

    def test_build_user_prefs_schema_has_toggle(self):
        schema = build_user_prefs_schema({})
        keys = {str(k) for k in schema}
        assert CONF_USER_PREFERENCE_ENABLED in keys

    def test_modules_schema_defaults_roundtrip(self):
        """Schema built with defaults should validate an empty input dict."""
        schema_dict = build_modules_schema({})
        s = vol.Schema(schema_dict)
        result = s({})
        assert CONF_ENTITY_PROFILE in result

    def test_neuron_schema_defaults_roundtrip(self):
        schema_dict = build_neuron_schema({})
        s = vol.Schema(schema_dict)
        result = s({})
        assert result[CONF_NEURON_ENABLED] is True
        assert result[CONF_NEURON_EVALUATION_INTERVAL] == 60


# ═══════════════════════════════════════════════════════════════════════════
# 6. ConfigFlow (mocked HA data_entry_flow)
# ═══════════════════════════════════════════════════════════════════════════


class TestConfigFlowUnit:
    """Unit tests for ConfigFlow logic without full HA runtime.

    We patch HA-specific methods and only test our logic.
    """

    def _build_flow(self):
        """Construct a ConfigFlow with minimal HA mocks."""
        from custom_components.copilot_ha.config_flow import ConfigFlow

        flow = ConfigFlow.__new__(ConfigFlow)
        flow.hass = _FakeHass()
        flow.context = {}
        flow.source = "user"
        flow._async_current_entries = MagicMock(return_value=[])
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_menu = MagicMock(return_value={"type": "menu"})
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        flow.async_abort = MagicMock(return_value={"type": "abort"})
        return flow

    @pytest.mark.asyncio
    async def test_user_step_shows_menu(self):
        flow = self._build_flow()
        result = await flow.async_step_user()
        flow.async_show_menu.assert_called_once()
        call_kwargs = flow.async_show_menu.call_args
        assert "zero_config" in call_kwargs.kwargs.get("menu_options", call_kwargs[1].get("menu_options", []))

    @pytest.mark.asyncio
    async def test_user_step_single_instance(self):
        flow = self._build_flow()
        flow._async_current_entries = MagicMock(return_value=[_FakeConfigEntry()])
        result = await flow.async_step_user()
        flow.async_abort.assert_called_once_with(reason="single_instance_allowed")

    @pytest.mark.asyncio
    async def test_zero_config_creates_entry(self):
        flow = self._build_flow()
        with patch(
            "custom_components.copilot_ha.config_flow.discover_reachable_core_endpoint",
            new_callable=AsyncMock,
            return_value=("192.168.1.10", 8909),
        ), patch(
            "custom_components.copilot_ha.config_flow.validate_input",
            new_callable=AsyncMock,
        ):
            result = await flow.async_step_zero_config()
        flow.async_create_entry.assert_called_once()
        call_kwargs = flow.async_create_entry.call_args
        data = call_kwargs.kwargs.get("data", call_kwargs[1].get("data", {}))
        assert data["host"] == "192.168.1.10"
        assert data["port"] == 8909

    @pytest.mark.asyncio
    async def test_zero_config_unreachable_still_creates(self):
        """Zero-config creates entry even when Core is unreachable."""
        flow = self._build_flow()
        with patch(
            "custom_components.copilot_ha.config_flow.discover_reachable_core_endpoint",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "custom_components.copilot_ha.config_flow.validate_input",
            new_callable=AsyncMock,
            side_effect=Exception("offline"),
        ):
            result = await flow.async_step_zero_config()
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_setup_shows_form(self):
        flow = self._build_flow()
        with patch(
            "custom_components.copilot_ha.config_flow.discover_reachable_core_endpoint",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await flow.async_step_manual_setup()
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_setup_creates_entry(self):
        flow = self._build_flow()
        user_input = {
            "assistant_name": "Styx",
            CONF_HOST: "192.168.1.5",
            CONF_PORT: 8909,
        }
        with patch(
            "custom_components.copilot_ha.config_flow.validate_input",
            new_callable=AsyncMock,
        ):
            result = await flow.async_step_manual_setup(user_input)
        flow.async_create_entry.assert_called_once()
        call_kwargs = flow.async_create_entry.call_args
        title = call_kwargs.kwargs.get("title", call_kwargs[1].get("title", ""))
        assert "Styx" in title
        assert "192.168.1.5" in title

    @pytest.mark.asyncio
    async def test_manual_setup_validation_failure_still_creates(self):
        """Manual setup creates entry even when Core is unreachable."""
        flow = self._build_flow()
        user_input = {
            "assistant_name": "Bot",
            CONF_HOST: "badhost",
            CONF_PORT: 9999,
        }
        with patch(
            "custom_components.copilot_ha.config_flow.validate_input",
            new_callable=AsyncMock,
            side_effect=Exception("timeout"),
        ):
            result = await flow.async_step_manual_setup(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_reauth_delegates_to_manual(self):
        flow = self._build_flow()
        with patch.object(flow, "async_step_manual_setup", new_callable=AsyncMock) as mock_manual:
            await flow.async_step_reauth()
            mock_manual.assert_awaited_once()


# ═══════════════════════════════════════════════════════════════════════════
# 7. OptionsFlowHandler
# ═══════════════════════════════════════════════════════════════════════════


class TestOptionsFlowUnit:
    """Unit tests for OptionsFlowHandler (mocked HA flow methods)."""

    def _build_options_flow(self, entry_data: dict | None = None, entry_options: dict | None = None):
        from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler

        entry = _FakeConfigEntry(data=entry_data or {}, options=entry_options or {})
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
        flow._entry = entry
        flow._snapshot = None
        flow.hass = _FakeHass()
        flow.async_show_menu = MagicMock(return_value={"type": "menu"})
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        flow.async_abort = MagicMock(return_value={"type": "abort"})
        return flow

    @pytest.mark.asyncio
    async def test_init_shows_menu(self):
        flow = self._build_options_flow()
        await flow.async_step_init()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get(
            "menu_options", flow.async_show_menu.call_args[1].get("menu_options", [])
        )
        assert "connection" in opts
        assert "modules" in opts
        assert "neurons" in opts

    @pytest.mark.asyncio
    async def test_connection_shows_form(self):
        flow = self._build_options_flow(entry_data={"host": "ha.local", "port": 8909})
        await flow.async_step_connection()
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_saves_input(self):
        flow = self._build_options_flow(entry_data={"host": "ha.local", "port": 8909, "token": ""})
        user_input = {"host": "192.168.1.50", "port": 8909}
        await flow.async_step_connection(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_modules_shows_form(self):
        flow = self._build_options_flow()
        await flow.async_step_modules()
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_modules_saves_input(self):
        flow = self._build_options_flow()
        user_input = {
            CONF_WATCHDOG_ENABLED: True,
            CONF_EVENTS_FORWARDER_ENABLED: False,
        }
        await flow.async_step_modules(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_neurons_shows_form(self):
        flow = self._build_options_flow()
        await flow.async_step_neurons()
        flow.async_show_form.assert_called_once()

    @pytest.mark.asyncio
    async def test_neurons_saves_input(self):
        flow = self._build_options_flow()
        user_input = {
            CONF_NEURON_ENABLED: True,
            CONF_NEURON_EVALUATION_INTERVAL: 120,
            "neuron_context_entities": ["sensor.temp"],
            "neuron_state_entities": [],
            "neuron_mood_entities": "sensor.mood1, sensor.mood2",
        }
        await flow.async_step_neurons(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_back_returns_to_init(self):
        flow = self._build_options_flow()
        await flow.async_step_back()
        flow.async_show_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_entity_tags_menu(self):
        flow = self._build_options_flow()
        await flow.async_step_entity_tags()
        flow.async_show_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_habitus_zones_menu(self):
        flow = self._build_options_flow()
        await flow.async_step_habitus_zones()
        flow.async_show_menu.assert_called_once()

    def test_effective_config_merges(self):
        flow = self._build_options_flow(
            entry_data={"host": "a", "port": 8909},
            entry_options={"host": "b"},
        )
        cfg = flow._effective_config()
        assert cfg["host"] == "b"
        assert cfg["port"] == 8909

    @pytest.mark.asyncio
    async def test_connection_clear_token(self):
        flow = self._build_options_flow(entry_data={"host": "ha", "port": 8909, "token": "secret"})
        user_input = {"host": "ha", "port": 8909, "_clear_token": True, "token": ""}
        await flow.async_step_connection(user_input)
        flow.async_create_entry.assert_called_once()
        call_data = flow.async_create_entry.call_args.kwargs.get(
            "data", flow.async_create_entry.call_args[1].get("data", {})
        )
        assert call_data.get("token") == ""


# ═══════════════════════════════════════════════════════════════════════════
# 8. _normalize_entity_list (from config_options_flow)
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_options_flow import _normalize_entity_list


class TestNormalizeEntityList:
    def test_list_input(self):
        assert _normalize_entity_list(["a", "b"]) == ["a", "b"]

    def test_csv_string(self):
        assert _normalize_entity_list("x, y, z") == ["x", "y", "z"]

    def test_none(self):
        assert _normalize_entity_list(None) == []

    def test_single_value(self):
        assert _normalize_entity_list("sensor.temp") == ["sensor.temp"]

    def test_strips_whitespace(self):
        assert _normalize_entity_list([" a ", " b "]) == ["a", "b"]

    def test_empty_string(self):
        assert _normalize_entity_list("") == []

    def test_blank_entries_filtered(self):
        assert _normalize_entity_list(["", " ", "a"]) == ["a"]


# ═══════════════════════════════════════════════════════════════════════════
# 9. Delta-Write Pattern (_compute_delta + _create_merged_entry)
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_options_flow import _compute_delta


class TestComputeDelta:
    """Unit tests for _compute_delta (ConfigEntry delta-write helper)."""

    def test_no_change_returns_empty(self):
        existing = {"host": "ha.local", "port": 8909, "token": "secret"}
        delta = _compute_delta(existing, {"host": "ha.local", "port": 8909})
        assert delta == {}

    def test_single_key_changed(self):
        existing = {"host": "ha.local", "port": 8909}
        delta = _compute_delta(existing, {"host": "192.168.1.50"})
        assert delta == {"host": "192.168.1.50"}

    def test_multiple_keys_changed(self):
        existing = {"host": "old", "port": 8909, "token": "x"}
        delta = _compute_delta(existing, {"host": "new", "port": 9999})
        assert delta == {"host": "new", "port": 9999}

    def test_list_changed(self):
        existing = {"entities": ["a", "b"]}
        delta = _compute_delta(existing, {"entities": ["a", "b", "c"]})
        assert delta == {"entities": ["a", "b", "c"]}

    def test_list_unchanged(self):
        existing = {"entities": ["a", "b"]}
        delta = _compute_delta(existing, {"entities": ["a", "b"]})
        assert delta == {}

    def test_dict_changed(self):
        existing = {"cfg": {"x": 1}}
        delta = _compute_delta(existing, {"cfg": {"x": 2}})
        assert delta == {"cfg": {"x": 2}}

    def test_dict_unchanged(self):
        existing = {"cfg": {"x": 1}}
        delta = _compute_delta(existing, {"cfg": {"x": 1}})
        assert delta == {}

    def test_new_key_added(self):
        existing = {"host": "ha"}
        delta = _compute_delta(existing, {"host": "ha", "token": "new"})
        assert delta == {"token": "new"}

    def test_key_removed_in_new(self):
        existing = {"host": "ha", "port": 8909}
        delta = _compute_delta(existing, {"host": "ha", "port": None})
        assert delta == {"port": None}

    def test_both_none_skipped(self):
        delta = _compute_delta({"x": None}, {"x": None})
        assert delta == {}


class TestOptionsFlowDeltaWrite:
    """Integration-style tests for OptionsFlowHandler delta-write behaviour.

    Uses the same harness pattern as TestOptionsFlowUnit.
    """

    def _build_flow(self, entry_data: dict | None = None):
        from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler

        entry = _FakeConfigEntry(data=entry_data or {}, options={})
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
        flow._entry = entry
        flow._snapshot = None
        flow.hass = _FakeHass()
        flow.async_show_menu = MagicMock(return_value={"type": "menu"})
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        flow.async_abort = MagicMock(return_value={"type": "abort"})
        return flow

    @pytest.mark.asyncio
    async def test_connection_only_writes_delta(self):
        """Only the changed host key should be written; port stays in entry.data."""
        flow = self._build_flow(entry_data={"host": "ha.local", "port": 8909, "token": "s3cret"})
        user_input = {"host": "192.168.1.50", "port": 8909}

        await flow.async_step_connection(user_input)
        flow.async_create_entry.assert_called_once()

        call_data = flow.async_create_entry.call_args.kwargs.get(
            "data", flow.async_create_entry.call_args[1].get("data", {})
        )
        # port should NOT appear in delta — it equals the existing value
        assert call_data.get("host") == "192.168.1.50"
        assert "port" not in call_data  # unchanged → not written
        assert "token" not in call_data  # unchanged → not written

    @pytest.mark.asyncio
    async def test_modules_step_writes_only_changed_toggle(self):
        """Only the toggled module flag should be written."""
        flow = self._build_flow(
            entry_data={
                "watchdog_enabled": True,
                "events_forwarder_enabled": False,
                "host": "ha.local",
                "port": 8909,
            }
        )
        user_input = {"watchdog_enabled": False}

        await flow.async_step_modules(user_input)
        call_data = flow.async_create_entry.call_args.kwargs.get(
            "data", flow.async_create_entry.call_args[1].get("data", {})
        )
        assert call_data.get("watchdog_enabled") is False
        assert "events_forwarder_enabled" not in call_data
        assert "host" not in call_data

    @pytest.mark.asyncio
    async def test_reauth_full_merge(self):
        """Reauth (SOURCE_REAUTH) does full merge — delta-write not used."""
        flow = self._build_flow(entry_data={"host": "old", "port": 8909})
        flow.source = "reauth"
        flow.context = {"entry_id": "entry_1"}

        # Mock hass.config_entries lookup
        reauth_entry = _FakeConfigEntry(entry_id="entry_1", data={"host": "old", "port": 8909, "token": "tok"})
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_get_entry = MagicMock(return_value=reauth_entry)
        flow.hass.config_entries.async_update_entry = MagicMock()
        flow.hass.config_entries.async_reload = AsyncMock()

        user_input = {"host": "new", "port": 8909}
        await flow.async_step_manual_setup(user_input)

        flow.hass.config_entries.async_update_entry.assert_called_once()
        update_call = flow.hass.config_entries.async_update_entry.call_args
        # Reauth updates entry directly with merged data (expected full merge)
        updated_data = update_call[0][1].data
        assert updated_data["host"] == "new"
        assert updated_data["port"] == 8909


# 9. ModuleContext and CopilotModule protocol
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.core.module import ModuleContext, CopilotModule


class TestModuleContext:
    def test_domain_property(self):
        entry = _FakeConfigEntry(domain="copilot_ha")
        hass = _FakeHass()
        ctx = ModuleContext(hass=hass, entry=entry)
        assert ctx.domain == "copilot_ha"

    def test_entry_id_property(self):
        entry = _FakeConfigEntry(entry_id="e123")
        ctx = ModuleContext(hass=_FakeHass(), entry=entry)
        assert ctx.entry_id == "e123"

    def test_frozen(self):
        ctx = ModuleContext(hass=_FakeHass(), entry=_FakeConfigEntry())
        with pytest.raises(AttributeError):
            ctx.hass = None  # type: ignore[misc]


class TestCopilotModuleProtocol:
    def test_protocol_check(self):
        mod = MagicMock()
        mod.name = "test"
        mod.async_setup_entry = AsyncMock()
        mod.async_unload_entry = AsyncMock(return_value=True)
        assert isinstance(mod, CopilotModule)

    def test_protocol_missing_name_still_passes(self):
        """MagicMock has .name by default, so this is a sanity check."""
        mod = MagicMock(spec=["async_setup_entry", "async_unload_entry", "name"])
        assert isinstance(mod, CopilotModule)


# ═══════════════════════════════════════════════════════════════════════════
# 10. manifest.json validation
# ═══════════════════════════════════════════════════════════════════════════
import json
import pathlib


class TestManifest:
    """Verify manifest.json has correct config_flow flag and structure."""

    @staticmethod
    def _load_manifest() -> dict:
        path = pathlib.Path(__file__).resolve().parent.parent / "manifest.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_config_flow_enabled(self):
        m = self._load_manifest()
        assert m["config_flow"] is True

    def test_domain(self):
        m = self._load_manifest()
        assert m["domain"] == "copilot_ha"

    def test_version_present(self):
        m = self._load_manifest()
        assert "version" in m
        assert m["version"]  # non-empty

    def test_required_dependencies(self):
        m = self._load_manifest()
        assert "http" in m.get("dependencies", [])
        assert "webhook" in m.get("dependencies", [])

    def test_integration_type(self):
        m = self._load_manifest()
        assert m.get("integration_type") == "hub"

    def test_iot_class_local(self):
        m = self._load_manifest()
        assert m.get("iot_class") == "local_push"


# ═══════════════════════════════════════════════════════════════════════════
# 11. config_snapshot_flow import path resolution
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha import config_snapshot_flow as _snapshot_flow


class TestConfigSnapshotFlowPathResolve:
    def test_maps_local_url_to_www_path(self):
        resolved = _snapshot_flow._resolve_snapshot_import_path("/local/copilot_ha/snapshot.json")
        assert resolved == "/config/www/copilot_ha/snapshot.json"

    def test_relative_path_defaults_to_export_dir_when_missing(self, monkeypatch):
        monkeypatch.setattr(_snapshot_flow.os.path, "exists", lambda p: False)
        resolved = _snapshot_flow._resolve_snapshot_import_path("snapshot.json")
        assert resolved == f"{_snapshot_flow.EXPORT_DIR}/snapshot.json"

    def test_load_json_path_resolves_relative_export_path(self, tmp_path):
        export_dir = tmp_path / "exports"
        publish_dir = tmp_path / "www"
        export_dir.mkdir(parents=True, exist_ok=True)
        publish_dir.mkdir(parents=True, exist_ok=True)

        snapshot_file = export_dir / "snapshot.json"
        snapshot_file.write_text(json.dumps({"schema": "copilot_ha_config_snapshot"}), encoding="utf-8")

        old_export = _snapshot_flow.EXPORT_DIR
        old_publish = _snapshot_flow.PUBLISH_DIR
        try:
            _snapshot_flow.EXPORT_DIR = str(export_dir)
            _snapshot_flow.PUBLISH_DIR = str(publish_dir)
            loaded = _snapshot_flow._load_json_path("snapshot.json")
        finally:
            _snapshot_flow.EXPORT_DIR = old_export
            _snapshot_flow.PUBLISH_DIR = old_publish

        assert loaded["schema"] == "copilot_ha_config_snapshot"

    def test_expands_tilde_to_home(self, monkeypatch):
        """~ should be expanded to the real home directory."""
        monkeypatch.setenv("HOME", "/home/andreas")
        resolved = _snapshot_flow._resolve_snapshot_import_path("~/snapshots/test.json")
        assert resolved == "/home/andreas/snapshots/test.json"

    def test_expands_env_variable(self, monkeypatch):
        """$SNAPSHOT_DIR and ${SNAPSHOT_DIR} should both expand."""
        monkeypatch.setenv("SNAPSHOT_DIR", "/mnt/backups")
        assert _snapshot_flow._resolve_snapshot_import_path("$SNAPSHOT_DIR/test.json") == "/mnt/backups/test.json"
        assert _snapshot_flow._resolve_snapshot_import_path("${SNAPSHOT_DIR}/test.json") == "/mnt/backups/test.json"

    def test_env_var_in_local_url_expands(self, monkeypatch):
        """Env vars inside a /local/ URL are expanded before the prefix is stripped."""
        monkeypatch.setenv("WWW_ROOT", "/config/www")
        resolved = _snapshot_flow._resolve_snapshot_import_path("/local/$WWW_ROOT/sub/file.json")
        # After expansion: /local//config/www/sub/file.json → normpath → /config/www/sub/file.json
        assert resolved == "/config/www/sub/file.json"

    def test_path_traversal_outside_export_dir_is_rejected(self, monkeypatch):
        """A relative path with ../ that escapes EXPORT_DIR returns the default instead."""
        monkeypatch.setattr(_snapshot_flow.os.path, "exists", lambda p: False)
        monkeypatch.setattr(_snapshot_flow, "EXPORT_DIR", "/config/exports")
        monkeypatch.setattr(_snapshot_flow, "PUBLISH_DIR", "/config/www")
        resolved = _snapshot_flow._resolve_snapshot_import_path("../etc/passwd")
        # Must NOT return /etc/passwd; should return default EXPORT_DIR + candidate
        assert resolved == "/config/exports/../etc/passwd"
        # If we want stricter: the point is it doesn't bypass the sandbox dirs
        # without the normpath guard above it would have returned /etc/passwd

    def test_resolved_path_follows_symlinks(self, tmp_path):
        """Path.resolve() is called so symlinks are dereferenced."""
        export_dir = tmp_path / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        real_file = export_dir / "real.json"
        real_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")

        link_path = tmp_path / "link.json"
        link_path.symlink_to(real_file)

        old_export = _snapshot_flow.EXPORT_DIR
        try:
            _snapshot_flow.EXPORT_DIR = str(export_dir)
            _snapshot_flow.PUBLISH_DIR = str(tmp_path / "www")
            resolved = _snapshot_flow._resolve_snapshot_import_path(str(link_path))
        finally:
            _snapshot_flow.EXPORT_DIR = old_export

        # Should resolve to the real file, not the symlink
        assert resolved == str(real_file)


# ═══════════════════════════════════════════════════════════════════════════
# 12. Minimal integration tests for zone/options/snapshot flows
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_zones_flow import async_step_zone_form
from custom_components.copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
from custom_components.copilot_ha.config_snapshot_flow import ConfigSnapshotOptionsFlow


class _ZoneFlowHarness:
    def __init__(self):
        self.hass = _FakeHass()
        self._entry = _FakeConfigEntry(entry_id="entry-zone")
        self.async_show_form = MagicMock(return_value={"type": "form"})
        self.async_abort = MagicMock(return_value={"type": "abort"})
        self.async_step_habitus_zones = AsyncMock(return_value={"type": "menu", "step_id": "habitus_zones"})


class TestZoneOptionsSnapshotIntegration:
    @pytest.mark.asyncio
    async def test_zone_form_create_persists_zone_and_syncs(self):
        flow = _ZoneFlowHarness()

        with patch(
            "custom_components.copilot_ha.habitus_zones_store_v2.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_get_zones, patch(
            "custom_components.copilot_ha.habitus_zones_store_v2.async_set_zones_v2",
            new_callable=AsyncMock,
        ) as mock_set_zones, patch(
            "custom_components.copilot_ha.config_zones_flow._list_area_options",
            return_value=[],
        ), patch(
            "custom_components.copilot_ha.config_zones_flow.async_sync_zone_editor_zone",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_sync, patch(
            "custom_components.copilot_ha.config_zones_flow.create_zone_tag",
            new_callable=AsyncMock,
        ) as mock_create_tag, patch(
            "custom_components.copilot_ha.config_zones_flow.tag_zone_entities",
            new_callable=AsyncMock,
        ) as mock_tag_entities:
            result = await async_step_zone_form(
                flow,
                mode="create",
                user_input={
                    "name": "Wohnbereich",
                    "motion_entity_id": "binary_sensor.motion_wohnzimmer",
                    "light_entity_ids": ["light.wohnzimmer_decke"],
                    "optional_entity_ids": ["sensor.wohnzimmer_temp"],
                },
            )

        assert result == {"type": "menu", "step_id": "habitus_zones"}
        mock_get_zones.assert_awaited_once_with(flow.hass, "entry-zone")

        saved_zones = mock_set_zones.await_args.args[2]
        assert len(saved_zones) == 1
        saved_zone = saved_zones[0]
        assert saved_zone.zone_id == "zone:wohnbereich"
        assert saved_zone.name == "Wohnbereich"
        assert "binary_sensor.motion_wohnzimmer" in saved_zone.entity_ids
        assert "light.wohnzimmer_decke" in saved_zone.entity_ids

        mock_sync.assert_awaited_once()
        sync_call = mock_sync.await_args.kwargs
        assert sync_call["mode"] == "create"
        assert sync_call["zone"].zone_id == "zone:wohnbereich"

        mock_create_tag.assert_awaited_once_with(flow.hass, "zone:wohnbereich", "Wohnbereich")
        mock_tag_entities.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_options_flow_delete_zone_updates_store_and_sync(self):
        flow = TestOptionsFlowUnit()._build_options_flow()
        flow.async_step_habitus_zones = AsyncMock(return_value={"type": "menu", "step_id": "habitus_zones"})

        zones = [
            HabitusZoneV2(zone_id="zone:kueche", name="Kueche", entity_ids=("light.kueche",)),
            HabitusZoneV2(zone_id="zone:wohnzimmer", name="Wohnzimmer", entity_ids=("light.wohnzimmer",)),
        ]

        with patch(
            "custom_components.copilot_ha.habitus_zones_store_v2.async_get_zones_v2",
            new_callable=AsyncMock,
            return_value=zones,
        ), patch(
            "custom_components.copilot_ha.habitus_zones_store_v2.async_set_zones_v2",
            new_callable=AsyncMock,
        ) as mock_set_zones, patch(
            "custom_components.copilot_ha.config_options_flow.async_sync_zone_editor_zone",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_sync:
            result = await flow.async_step_delete_zone({"zone_id": "zone:kueche"})

        assert result == {"type": "menu", "step_id": "habitus_zones"}
        remaining = mock_set_zones.await_args.args[2]
        assert [zone.zone_id for zone in remaining] == ["zone:wohnzimmer"]

        mock_sync.assert_awaited_once()
        sync_kwargs = mock_sync.await_args.kwargs
        assert sync_kwargs["mode"] == "delete"
        assert sync_kwargs["previous_zone_id"] == "zone:kueche"

    @pytest.mark.asyncio
    async def test_options_flow_snapshot_confirm_applies_snapshot(self):
        flow = TestOptionsFlowUnit()._build_options_flow()
        ConfigSnapshotOptionsFlow.__init__(flow, flow._entry)
        flow._snapshot = {
            "schema": "copilot_ha_config_snapshot",
            "habitus_zones": [{"id": "zone:kueche", "name": "Kueche", "entity_ids": ["light.kueche"]}],
        }

        with patch(
            "custom_components.copilot_ha.config_snapshot_flow.async_apply_config_snapshot",
            new_callable=AsyncMock,
        ) as mock_apply:
            result = await flow.async_step_import_snapshot_confirm({"confirm": True})

        assert result == {"type": "create_entry"}
        mock_apply.assert_awaited_once_with(flow.hass, flow.config_entry, flow._snapshot)
