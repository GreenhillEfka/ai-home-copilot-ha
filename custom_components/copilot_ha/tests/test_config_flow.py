"""Tests for PilotSuite Config Flow, Options Flow, and Module Registry.

Covers:
- ConfigFlow: zero_config, manual_setup, reauth, single-instance guard
- OptionsFlowHandler: init menu, connection, modules, neurons
- ModuleRegistry: register, create, names, duplicate, unknown
- CopilotRuntime: get singleton, setup_entry, unload_entry
- config_helpers: parse_csv, as_csv, merge_config_data, validate_input
- config_schema_builders: build_modules_schema, build_neuron_schema
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

    # ── Reconfigure helpers ────────────────────────────────────────────

    def _build_reconfigure_flow(self, entry_data: dict | None = None, entry_options: dict | None = None):
        """Construct a ConfigFlow in reconfigure mode, bound to a fake entry."""
        from custom_components.copilot_ha.config_flow import ConfigFlow

        entry = _FakeConfigEntry(
            data=entry_data or {"host": "192.168.1.10", "port": 8909, "token": "tok"},
            options=entry_options or {},
        )
        flow = ConfigFlow.__new__(ConfigFlow)
        flow.hass = _FakeHass()
        object.__setattr__(flow, "context", {"source": "reconfigure", "config_entry_id": entry.entry_id})
        flow._entry = entry
        flow._async_current_entries = MagicMock(return_value=[])
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_show_menu = MagicMock(return_value={"type": "menu"})
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
        flow.async_abort = MagicMock(return_value={"type": "abort"})
        flow._get_reconfigure_entry = MagicMock(return_value=entry)
        return flow

    @pytest.mark.asyncio
    async def test_reconfigure_step_shows_menu(self):
        """async_step_reconfigure shows the reconfigure menu with connection/zones/back."""
        flow = self._build_reconfigure_flow()
        result = await flow.async_step_reconfigure()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get(
            "menu_options", flow.async_show_menu.call_args[1].get("menu_options", [])
        )
        assert "reconfigure_connection" in opts
        assert "reconfigure_zones" in opts
        assert "back" in opts

    @pytest.mark.asyncio
    async def test_reconfigure_seeds_reconfigure_data(self):
        """Reconfigure seeds ConfigFlow._reconfigure_data from entry data."""
        flow = self._build_reconfigure_flow(
            entry_data={"host": "10.0.0.1", "port": 9000, "token": "mytok"},
        )
        from custom_components.copilot_ha.config_flow import ConfigFlow

        ConfigFlow._reconfigure_data = {}
        await flow.async_step_reconfigure()
        assert ConfigFlow._reconfigure_data.get("host") == "10.0.0.1"
        assert ConfigFlow._reconfigure_data.get("port") == 9000
        assert ConfigFlow._reconfigure_data.get("token") == "mytok"

    @pytest.mark.asyncio
    async def test_reconfigure_connection_shows_form(self):
        """Reconfigure connection step renders the form on first call (user_input=None)."""
        flow = self._build_reconfigure_flow(
            entry_data={"host": "192.168.1.10", "port": 8909, "token": "tok"},
        )
        result = await flow.async_step_reconfigure_connection()
        flow.async_show_form.assert_called_once()
        step_id = flow.async_show_form.call_args.kwargs.get("step_id")
        assert step_id == "reconfigure_connection"

    @pytest.mark.asyncio
    async def test_reconfigure_connection_accumulates_params(self):
        """Reconfigure connection accumulates host/port/token in _reconfigure_data."""
        flow = self._build_reconfigure_flow(
            entry_data={"host": "old.local", "port": 8909, "token": "old"},
        )
        from custom_components.copilot_ha.config_flow import ConfigFlow

        ConfigFlow._reconfigure_data = {}
        user_input = {"host": "new.local", "port": 9000, "token": "new"}
        result = await flow.async_step_reconfigure_connection(user_input)
        # After save, shows menu again
        flow.async_show_menu.assert_called()
        assert ConfigFlow._reconfigure_data.get("host") == "new.local"
        assert ConfigFlow._reconfigure_data.get("port") == 9000

    @pytest.mark.asyncio
    async def test_reconfigure_back_commits_and_returns_menu(self):
        """Back step commits _reconfigure_data to entry and returns to menu."""
        flow = self._build_reconfigure_flow(
            entry_data={"host": "192.168.1.10", "port": 8909, "token": "tok"},
        )
        from custom_components.copilot_ha.config_flow import ConfigFlow

        ConfigFlow._reconfigure_data = {"host": "committed.local", "port": 8123}
        # Mock hass.config_entries.async_update_entry
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_update_entry = MagicMock()

        result = await flow.async_step_back()
        flow.hass.config_entries.async_update_entry.assert_called_once()
        call_args = flow.hass.config_entries.async_update_entry.call_args
        updated_entry = call_args[0][0]
        assert updated_entry is flow._entry
        updated_data = call_args[0][1]
        assert updated_data["host"] == "committed.local"
        assert updated_data["port"] == 8123
        # Staging dict should be cleared
        assert ConfigFlow._reconfigure_data == {}


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
# 11. config_zones_flow helpers
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_zones_flow import (
    _normalize_entity_ids,
    _normalize_area_ids,
    _slugify,
    _zone_id_from_name,
    _ensure_unique_zone_id,
)


class TestZonesFlowHelpers:
    """Unit tests for zone flow pure helpers (no HA runtime needed)."""

    def test_normalize_entity_ids_none(self):
        assert _normalize_entity_ids(None) == []

    def test_normalize_entity_ids_list(self):
        assert _normalize_entity_ids(["a", "b"]) == ["a", "b"]

    def test_normalize_entity_ids_string(self):
        assert _normalize_entity_ids("sensor.temp") == ["sensor.temp"]

    def test_normalize_entity_ids_string_trims(self):
        assert _normalize_entity_ids("  sensor.temp  ") == ["sensor.temp"]

    def test_normalize_entity_ids_string_comma_sep_strips(self):
        assert _normalize_entity_ids("a, b, c") == ["a, b, c"]  # no csv split here

    def test_normalize_entity_ids_filters_empty(self):
        assert _normalize_entity_ids(["", "  ", "a"]) == ["a"]

    def test_normalize_area_ids_none(self):
        assert _normalize_area_ids(None) == []

    def test_normalize_area_ids_list_dedupe(self):
        assert _normalize_area_ids(["area_1", "area_2", "area_1"]) == ["area_1", "area_2"]

    def test_normalize_area_ids_string(self):
        assert _normalize_area_ids("kitchen") == ["kitchen"]

    def test_normalize_area_ids_filters_duplicates(self):
        assert _normalize_area_ids(["a", "a", "b"]) == ["a", "b"]

    def test_slugify_basic(self):
        assert _slugify("Wohnzimmer") == "wohnzimmer"

    def test_slugify_spaces_to_underscores(self):
        assert _slugify("Mein Bereich") == "mein_bereich"

    def test_slugify_umlauts_ascii(self):
        assert _slugify("Küche") == "kuche"

    def test_slugify_fallback_empty(self):
        assert _slugify("---") == "zone"

    def test_zone_id_from_name_plain(self):
        zid = _zone_id_from_name("Kitchen")
        assert zid == "zone:kitchen"

    def test_zone_id_from_name_already_zone_prefix(self):
        zid = _zone_id_from_name("zone:kitchen")
        assert zid == "zone:kitchen"

    def test_ensure_unique_zone_id_free(self):
        existing = {"zone:kitchen", "zone:bedroom"}
        assert _ensure_unique_zone_id("zone:bathroom", existing) == "zone:bathroom"

    def test_ensure_unique_zone_id_collision(self):
        existing = {"zone:kitchen", "zone:kitchen_2"}
        assert _ensure_unique_zone_id("zone:kitchen", existing) == "zone:kitchen_3"


# ═══════════════════════════════════════════════════════════════════════════
# 12. OptionsFlowHandler — zones, tags, snapshot import (integration layer)
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler


class TestOptionsFlowZonesAndTags:
    """Integration-level tests: OptionsFlow zone + tag steps with real store.

    Uses conftest fixtures: make_options_flow, config_entry_with_data, mock_hass.
    """

    @pytest.mark.asyncio
    async def test_habitus_zones_menu(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_habitus_zones()
        assert flow.async_show_menu.called
        opts = flow.async_show_menu.call_args.kwargs.get("menu_options", [])
        assert "create_zone" in opts
        assert "edit_zone" in opts
        assert "delete_zone" in opts
        assert "back" in opts

    @pytest.mark.asyncio
    async def test_create_zone_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        """Create-zone step shows the zone form (no HA area registry → empty area selector)."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_create_zone()
        # async_step_zone_form always shows form when user_input is None
        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args.kwargs
        assert call_kwargs.get("step_id") == "create_zone"

    @pytest.mark.asyncio
    async def test_edit_zone_aborts_without_zones(self, make_options_flow, config_entry_with_data, mock_hass):
        """Edit zone aborts when no zones exist in store."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_edit_zone()
        flow.async_abort.assert_called_once()
        assert flow.async_abort.call_args.kwargs.get("reason") == "no_zones"

    @pytest.mark.asyncio
    async def test_delete_zone_aborts_without_zones(self, make_options_flow, config_entry_with_data, mock_hass):
        """Delete zone aborts when no zones exist in store."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_delete_zone()
        flow.async_abort.assert_called_once()
        assert flow.async_abort.call_args.kwargs.get("reason") == "no_zones"

    @pytest.mark.asyncio
    async def test_entity_tags_menu(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_entity_tags()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get("menu_options", [])
        assert "add_tag" in opts
        assert "edit_tag" in opts
        assert "delete_tag" in opts
        assert "back" in opts

    @pytest.mark.asyncio
    async def test_automation_modes_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        """Automation modes step renders the form (empty zone list → only global mode)."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_automation_modes()
        flow.async_show_form.assert_called_once()
        step_id = flow.async_show_form.call_args.kwargs.get("step_id")
        assert step_id == "automation_modes"

    @pytest.mark.asyncio
    async def test_back_from_habitus_zones_returns_to_init(
        self, make_options_flow, config_entry_with_data, mock_hass
    ):
        """Back from habitus_zones → init menu."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_back()
        flow.async_show_menu.assert_called()
        # async_step_back delegates based on context
        call_kwargs = flow.async_show_menu.call_args.kwargs
        # Either reconfigure_menu or init
        assert call_kwargs.get("step_id") in ("reconfigure_menu", "init")


# ═══════════════════════════════════════════════════════════════════════════
# 13. OptionsFlowHandler — reconfigure flow (HA 2024.4+)
# ═══════════════════════════════════════════════════════════════════════════


class TestOptionsFlowReconfigure:
    """Test reconfigure entry point and sub-steps."""

    @pytest.mark.asyncio
    async def test_reconfigure_menu(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        flow.context = {"reconfigure": True}
        result = await flow.async_step_reconfigure()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get("menu_options", [])
        assert "reconfigure_connection" in opts
        assert "reconfigure_zones" in opts

    @pytest.mark.asyncio
    async def test_reconfigure_back_flushes_pending_params(
        self, make_options_flow, config_entry_with_data, mock_hass
    ):
        """Back navigation from reconfigure flushes pending shared params."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        flow.context = {"reconfigure": True}
        OptionsFlowHandler._pending_shared_params = {"host": "192.168.1.99"}
        await flow.async_step_reconfigure_back()
        # After flush, params should be cleared
        assert OptionsFlowHandler._pending_shared_params == {}

    @pytest.mark.asyncio
    async def test_reconfigure_connection_saves_pending(
        self, make_options_flow, config_entry_with_data, mock_hass
    ):
        """Reconfigure connection stages params in _pending_shared_params."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        flow.context = {"reconfigure": True}
        user_input = {"host": "192.168.1.50", "port": 8909}
        result = await flow.async_step_reconfigure_connection(user_input)
        # _pending_shared_params should have host/port
        pending = OptionsFlowHandler._pending_shared_params
        assert pending.get("host") == "192.168.1.50"
        assert pending.get("port") == 8909

    @pytest.mark.asyncio
    async def test_reconfigure_connection_shows_form_no_input(
        self, make_options_flow, config_entry_with_data, mock_hass
    ):
        """Reconfigure connection shows form on first call (user_input=None)."""
        flow = make_options_flow(config_entry_with_data, mock_hass)
        flow.context = {"reconfigure": True}
        result = await flow.async_step_reconfigure_connection()
        flow.async_show_form.assert_called_once()
        step_id = flow.async_show_form.call_args.kwargs.get("step_id")
        assert step_id == "reconfigure_connection"


# ═══════════════════════════════════════════════════════════════════════════
# 14. OptionsFlowHandler — module / neuron / LLM steps
# ═══════════════════════════════════════════════════════════════════════════


class TestOptionsFlowModulesAndNeurons:
    """Verify module, LLM provider, neuron, and autonomy steps show form and save."""

    @pytest.mark.asyncio
    async def test_modules_step_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_modules()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "modules"

    @pytest.mark.asyncio
    async def test_modules_step_saves_input(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        user_input = {"enable_suggest": True, "enable_forwarder": False}
        result = await flow.async_step_modules(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_provider_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_llm_provider()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "llm_provider"

    @pytest.mark.asyncio
    async def test_llm_provider_saves_input(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        user_input = {
            "llm_prefer_local": True,
            "llm_ollama_model": "llama3",
            "llm_cloud_api_url": "",
            "llm_cloud_api_key": "",
            "llm_cloud_model": "",
        }
        await flow.async_step_llm_provider(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_neurons_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_neurons()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "neurons"

    @pytest.mark.asyncio
    async def test_neurons_saves_entity_lists(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        user_input = {
            "neuron_enabled": True,
            "neuron_evaluation_interval": 60,
            "neuron_context_entities": ["sensor.temp", "sensor.humidity"],
            "neuron_state_entities": "binary_sensor.motion, binary_sensor.door",
            "neuron_mood_entities": [],
        }
        await flow.async_step_neurons(user_input)
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_autonomy_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_autonomy()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "autonomy"

    @pytest.mark.asyncio
    async def test_knowledge_graph_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_knowledge_graph()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "knowledge_graph"

    @pytest.mark.asyncio
    async def test_zone_health_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_zone_health()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "zone_health"

    @pytest.mark.asyncio
    async def test_ml_anomaly_shows_form(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_ml_anomaly()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "ml_anomaly"


# ═══════════════════════════════════════════════════════════════════════════
# 15. ConfigSnapshotOptionsFlow — import / export paths
# ═══════════════════════════════════════════════════════════════════════════
from custom_components.copilot_ha.config_snapshot_flow import (
    ConfigSnapshotOptionsFlow,
)


class TestSnapshotFlow:
    """Test ConfigSnapshotOptionsFlow import paths and error handling.

    Uses conftest fixture: make_snapshot (aka make_snapshot_flow).
    """

    @pytest.mark.asyncio
    async def test_backup_restore_menu(self, make_snapshot, config_entry_with_data, mock_hass):
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_backup_restore()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get("menu_options", [])
        assert "import_snapshot" in opts
        assert "back" in opts

    @pytest.mark.asyncio
    async def test_import_snapshot_shows_source_form(self, make_snapshot, config_entry_with_data, mock_hass):
        """First import step shows source selector (path vs paste)."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_import_snapshot()
        flow.async_show_form.assert_called_once()
        step_id = flow.async_show_form.call_args.kwargs.get("step_id")
        assert step_id == "import_snapshot"

    @pytest.mark.asyncio
    async def test_import_snapshot_path_shows_form(self, make_snapshot, config_entry_with_data, mock_hass):
        """Import path step shows file-path form."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_import_snapshot_path()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "import_snapshot_path"

    @pytest.mark.asyncio
    async def test_import_snapshot_path_invalid_path_error(self, make_snapshot, config_entry_with_data, mock_hass):
        """Invalid file path sets error and re-shows form."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_import_snapshot_path({"path": "/nonexistent/snapshot.json"})
        errors = flow.async_show_form.call_args.kwargs.get("errors", {})
        assert errors.get("base") == "cannot_read"

    @pytest.mark.asyncio
    async def test_import_snapshot_paste_shows_form(self, make_snapshot, config_entry_with_data, mock_hass):
        """Paste import step shows JSON textarea form."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_import_snapshot_paste()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "import_snapshot_paste"

    @pytest.mark.asyncio
    async def test_import_snapshot_paste_invalid_json_error(self, make_snapshot, config_entry_with_data, mock_hass):
        """Malformed JSON in paste shows invalid_json error."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        result = await flow.async_step_import_snapshot_paste({"json": "not valid { json"})
        errors = flow.async_show_form.call_args.kwargs.get("errors", {})
        assert errors.get("base") == "invalid_json"

    @pytest.mark.asyncio
    async def test_import_snapshot_confirm_shows_form(self, make_snapshot, config_entry_with_data, mock_hass):
        """Confirm step shows confirm form with zone preview."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        flow._snapshot = {"habitus_zones": [{"name": "Kitchen", "zone_id": "zone:kitchen"}]}
        result = await flow.async_step_import_snapshot_confirm()
        flow.async_show_form.assert_called_once()
        assert flow.async_show_form.call_args.kwargs.get("step_id") == "import_snapshot_confirm"

    @pytest.mark.asyncio
    async def test_import_snapshot_confirm_requires_checkbox(
        self, make_snapshot, config_entry_with_data, mock_hass
    ):
        """Confirm step with confirm=False returns error."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        flow._snapshot = {"habitus_zones": []}
        result = await flow.async_step_import_snapshot_confirm({"confirm": False})
        errors = flow.async_show_form.call_args.kwargs.get("errors", {})
        assert errors.get("base") == "confirm_required"

    @pytest.mark.asyncio
    async def test_import_snapshot_confirm_applies_and_creates_entry(
        self, make_snapshot, config_entry_with_data, mock_hass
    ):
        """Confirm with confirm=True calls async_apply_config_snapshot and creates entry."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        flow._snapshot = {"habitus_zones": [{"name": "Bedroom", "zone_id": "zone:bedroom"}]}
        with __import__("unittest.mock").patch(
            "custom_components.copilot_ha.config_snapshot.async_apply_config_snapshot",
            new_callable=AsyncMock,
        ) as mock_apply:
            result = await flow.async_step_import_snapshot_confirm({"confirm": True})
        mock_apply.assert_awaited_once()
        flow.async_create_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_import_snapshot_paste_accepts_valid_dict(self, make_snapshot, config_entry_with_data, mock_hass):
        """Valid dict JSON in paste stores snapshot and advances to confirm."""
        flow = make_snapshot(config_entry_with_data, mock_hass)
        valid_json = '{"habitus_zones": [{"name": "Office", "zone_id": "zone:office"}]}'
        result = await flow.async_step_import_snapshot_paste({"json": valid_json})
        # Should advance to confirm (calls async_show_form with step_id=import_snapshot_confirm)
        flow.async_show_form.assert_called()
        step_id = flow.async_show_form.call_args.kwargs.get("step_id")
        assert step_id == "import_snapshot_confirm"


# ═══════════════════════════════════════════════════════════════════════════
# 16. Connection step (make_options_flow already covers the basics, add save path)
# ═══════════════════════════════════════════════════════════════════════════


class TestOptionsFlowConnectionSave:
    """Verify connection step saves host/port/token changes."""

    @pytest.mark.asyncio
    async def test_connection_step_saves_host_and_port(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        user_input = {"host": "192.168.1.200", "port": 9000, "token": ""}
        await flow.async_step_connection(user_input)
        flow.async_create_entry.assert_called_once()
        call_data = flow.async_create_entry.call_args.kwargs.get("data", {})
        assert call_data.get("host") == "192.168.1.200"
        assert call_data.get("port") == 9000

    @pytest.mark.asyncio
    async def test_connection_step_clear_token(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        user_input = {"host": "192.168.1.10", "port": 8909, "_clear_token": True, "token": ""}
        await flow.async_step_connection(user_input)
        call_data = flow.async_create_entry.call_args.kwargs.get("data", {})
        assert call_data.get("token") == ""

    @pytest.mark.asyncio
    async def test_init_shows_all_menu_options(self, make_options_flow, config_entry_with_data, mock_hass):
        flow = make_options_flow(config_entry_with_data, mock_hass)
        result = await flow.async_step_init()
        flow.async_show_menu.assert_called_once()
        opts = flow.async_show_menu.call_args.kwargs.get("menu_options", [])
        # Check presence of key menu items (exact set may vary by version)
        assert "connection" in opts
        assert "modules" in opts
        assert "neurons" in opts
        assert "habitus_zones" in opts
