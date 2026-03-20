"""Shared test fixtures for all PilotSuite ConfigFlow tests.

Provides:
- MockHass         : FakeHass — no HA import, no __init__ interception
- ConfigEntry      : dataclass mimicking config_entries.ConfigEntry
- config_entry     : empty ConfigEntry fixture
- config_entry_with_data : ConfigEntry with standard connection data
- make_config_flow_handler()  : ConfigFlow handler with all HA methods mocked
- make_options_flow_handler() : OptionsFlowHandler with HA methods mocked
- make_snapshot_flow()        : ConfigSnapshotOptionsFlow with HA methods mocked
- mock_module_registry()      : clean ModuleRegistry + helpers
- mock_module()               : MagicMock satisfying CopilotModule protocol

All classes/factories are importable directly from this module so tests can
call them without going through pytest's fixture engine.
pytest-homeassistant-custom-component pattern: shared conftest at component level,
with per-test-class or per-test-function usage via import.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest  # noqa: F401 — activates @pytest.fixture decorators

# ──────────────────────────────────────────────────────────────────────────────
# Ensure the custom_component package resolves on all import paths
# (venv, CI container, bare python).
# ──────────────────────────────────────────────────────────────────────────────

THIS_FILE = Path(__file__).resolve()
COMPONENT_ROOT = THIS_FILE.parent.parent  # …/custom_components/copilot_ha
if str(COMPONENT_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPONENT_ROOT))

# ──────────────────────────────────────────────────────────────────────────────
# 1.  Minimal HA stubs  (replace inline stubs that lived scattered in test files)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class ConfigEntry:
    """Minimal ConfigEntry mimic — dataclass, not HA's class."""

    entry_id: str = "test_entry_1"
    domain: str = "copilot_ha"
    title: str = "Styx — PilotSuite"
    data: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    state: str = "loaded"
    minor_version: int = 1
    version: int = 1

    def __post_init__(self):
        if not isinstance(self.data, dict):
            self.data = {}
        if not isinstance(self.options, dict):
            self.options = {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "domain": self.domain,
            "title": self.title,
            "data": self.data,
            "options": self.options,
            "state": self.state,
            "version": self.version,
            "minor_version": self.minor_version,
        }


class MockHass:
    """Minimal hass stub — no HA import, no __init_subclass__ interference."""

    def __init__(self, **extra: Any) -> None:
        self.data: dict[str, Any] = {}
        self.config = MagicMock()
        self.config.internal_url = None
        self.config.external_url = None
        self.config_entries = MagicMock()
        self.config_entries.async_get_entry = MagicMock(return_value=None)
        for k, v in extra.items():
            setattr(self, k, v)


# ──────────────────────────────────────────────────────────────────────────────
# 2.  Pytest fixtures  (consume the classes above)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_hass() -> MockHass:
    """Fresh MockHass instance with empty data store."""
    return MockHass()


@pytest.fixture
def config_entry() -> ConfigEntry:
    """Minimal ConfigEntry with empty data/options."""
    return ConfigEntry()


@pytest.fixture
def config_entry_with_data() -> ConfigEntry:
    """ConfigEntry pre-loaded with standard connection data."""
    return ConfigEntry(
        entry_id="entry_with_data",
        data={
            "host": "192.168.1.10",
            "port": 8909,
            "token": "test_token_abc",
            "assistant_name": "Styx",
            "entity_profile": "default",
        },
    )


# ── ConfigFlow ────────────────────────────────────────────────────────────────


def make_config_flow_handler(
    hass: MockHass | None = None,
) -> Any:
    """Build a ConfigFlow instance with all HA data-entry-flow methods mocked.

    Usage::

        flow = make_config_flow_handler(hass)
        result = await flow.async_step_user()
        assert flow.async_show_menu.called

    Or via pytest fixture::

        def test_something(mock_hass):
            flow = make_config_flow_handler(mock_hass)
            ...
    """
    from custom_components.copilot_ha.config_flow import ConfigFlow

    if hass is None:
        hass = MockHass()

    flow = ConfigFlow.__new__(ConfigFlow)
    flow.hass = hass
    # HA 2024.3.3: source/context are read-only properties on ConfigFlow.
    # source is a read-only @property that reads self.context["source"].
    # Set context via __setattr__ then assign fields directly.
    object.__setattr__(flow, "context", {"source": "user"})
    flow._async_current_entries = MagicMock(return_value=[])
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})
    return flow


@pytest.fixture
def make_config_flow():
    """Pytest-compatible wrapper: returns the factory so tests get a fresh instance."""
    return make_config_flow_handler


# ── OptionsFlowHandler ────────────────────────────────────────────────────────


def make_options_flow_handler(
    entry: ConfigEntry | None = None,
    hass: MockHass | None = None,
) -> Any:
    """Build an OptionsFlowHandler bound to a ConfigEntry, with HA methods mocked.

    Usage::

        flow = make_options_flow_handler(entry, hass)
        result = await flow.async_step_init()
        assert flow.async_show_menu.called
    """
    from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler

    if entry is None:
        entry = ConfigEntry()
    if hass is None:
        hass = MockHass()

    # Patch __init__ so we can call __new__ without running HA's __init__
    # (which would call ConfigSnapshotOptionsFlow.__init__ and need hass context).
    with _patch_init(OptionsFlowHandler, lambda self, cfg: None):
        flow = OptionsFlowHandler.__new__(OptionsFlowHandler)

    flow._entry = entry
    flow._snapshot = None
    flow.hass = hass
    flow.context: dict[str, Any] = {}
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})
    return flow


@pytest.fixture
def make_options_flow():
    return make_options_flow_handler


# ── ConfigSnapshotOptionsFlow ──────────────────────────────────────────────────


def make_snapshot_flow(
    entry: ConfigEntry | None = None,
    hass: MockHass | None = None,
) -> Any:
    """Build a ConfigSnapshotOptionsFlow bound to a ConfigEntry, HA methods mocked.

    Usage::

        flow = make_snapshot_flow(entry, hass)
        result = await flow.async_step_backup_restore()
        assert flow.async_show_menu.called
    """
    from custom_components.copilot_ha.config_snapshot_flow import (
        ConfigSnapshotOptionsFlow,
    )

    if entry is None:
        entry = ConfigEntry()
    if hass is None:
        hass = MockHass()

    with _patch_init(ConfigSnapshotOptionsFlow, lambda self, cfg: None):
        flow = ConfigSnapshotOptionsFlow.__new__(ConfigSnapshotOptionsFlow)

    flow._entry = entry
    flow._snapshot = None
    flow.hass = hass
    flow.context: dict[str, Any] = {}
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})
    return flow


@pytest.fixture
def make_snapshot():
    return make_snapshot_flow


# ── Internal helpers ──────────────────────────────────────────────────────────

from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def _patch_init(klass, replacement):
    """Temporarily replace klass.__init__ so __new__ bypasses the original."""
    original = klass.__init__
    klass.__init__ = replacement
    try:
        yield
    finally:
        klass.__init__ = original


# ── Module registry helpers ───────────────────────────────────────────────────


def mock_module_registry() -> Any:
    """Clean ModuleRegistry with helper wrappers for test readability.

    Returns a ModuleRegistry with two extra convenience methods:
      .register(name, factory)  — add a module to the registry
      .make(name)               — alias for .create(name)

    Usage::

        reg = mock_module_registry()
        reg.register("alpha", lambda: mock_module("alpha"))
        mod = reg.make("alpha")
    """
    from custom_components.copilot_ha.core.registry import ModuleRegistry

    reg = ModuleRegistry()

    # Wrap original methods so test code uses descriptive names
    # instead of accidentally calling the wrapper recursively.
    _orig_register = reg.register
    _orig_create = reg.create

    def _register(name: str, factory) -> None:
        _orig_register(name, factory)

    def _make(name: str):
        return _orig_create(name)

    reg.register = _register
    reg.make = _make
    return reg


@pytest.fixture
def mock_module_registry_fixture():
    return mock_module_registry


def mock_module(name: str = "stub") -> MagicMock:
    """Returns a MagicMock that satisfies the CopilotModule protocol."""
    m = MagicMock()
    m.name = name
    m.async_setup_entry = AsyncMock()
    m.async_unload_entry = AsyncMock(return_value=True)
    return m


@pytest.fixture
def mock_module_fixture():
    return mock_module


# ──────────────────────────────────────────────────────────────────────────────
# 3.  Pytest configuration
# ──────────────────────────────────────────────────────────────────────────────

pytest_plugins = []


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: unit tests (no HA runtime)")
    config.addinivalue_line("markers", "integration: integration tests (full HA)")
