"""Pytest fixtures for PilotSuite Config Flow tests.

This module provides standardized pytest fixtures following the
pytest-homeassistant-custom-component pattern for testing PilotSuite
Config Flows and Options Flows.

Usage:
    Tests can use these fixtures directly:
    
    async def test_something(hass, config_entry, mock_config_flow):
        # Use fixtures...
        pass
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol


# ═══════════════════════════════════════════════════════════════════════════
# Fake HA Objects (Lightweight stubs for unit tests)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class FakeConfigEntry:
    """Minimal config entry stub for tests."""

    entry_id: str = "test_entry_1"
    domain: str = "copilot_ha"
    data: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)
    title: str = "Test Entry"
    unique_id: str | None = None
    state: str = "loaded"  # loaded, setup_retry, not_loaded

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.options is None:
            self.options = {}


class FakeHass:
    """Minimal hass stub for tests that need hass.data / hass.config."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.config = MagicMock()
        self.config.internal_url = None
        self.config.external_url = None
        self.config_entries = MagicMock()
        self.config_entries.async_get_entry = MagicMock(return_value=None)
        self.config_entries.async_update_entry = MagicMock()
        self.config_entries.async_reload = AsyncMock()


# ═══════════════════════════════════════════════════════════════════════════
# Core Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def hass() -> FakeHass:
    """Return a minimal FakeHass instance for unit tests."""
    return FakeHass()


@pytest.fixture
def config_entry() -> FakeConfigEntry:
    """Return a default FakeConfigEntry for testing."""
    return FakeConfigEntry()


@pytest.fixture
def config_entry_with_data() -> FakeConfigEntry:
    """Return a FakeConfigEntry with sample connection data."""
    return FakeConfigEntry(
        entry_id="test_entry_123",
        data={
            "host": "192.168.1.100",
            "port": 8909,
            "token": "test_token_123",
            "assistant_name": "Styx",
            "entity_profile": "standard",
        },
        options={
            "neuron_enabled": True,
            "neuron_evaluation_interval": 60,
        },
    )


# ═══════════════════════════════════════════════════════════════════════════
# Config Flow Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_config_flow(hass: FakeHass):
    """Build a ConfigFlow instance with mocked HA methods.
    
    Returns a ConfigFlow instance with all HA-specific methods mocked
    for isolated unit testing.
    """
    from custom_components.copilot_ha.config_flow import ConfigFlow

    flow = ConfigFlow.__new__(ConfigFlow)
    flow.hass = hass
    flow.context = {}
    flow.source = "user"

    # Mock HA flow methods
    flow._async_current_entries = MagicMock(return_value=[])
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})

    return flow


@pytest.fixture
def mock_config_flow_with_entry(hass: FakeHass, config_entry: FakeConfigEntry):
    """Build a ConfigFlow instance that reports an existing entry.
    
    Useful for testing single-instance guard behavior.
    """
    from custom_components.copilot_ha.config_flow import ConfigFlow

    flow = ConfigFlow.__new__(ConfigFlow)
    flow.hass = hass
    flow.context = {}
    flow.source = "user"

    # Report existing entry
    flow._async_current_entries = MagicMock(return_value=[config_entry])
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})

    return flow


@pytest.fixture
def mock_config_flow_reauth(hass: FakeHass, config_entry: FakeConfigEntry):
    """Build a ConfigFlow instance configured for reauth flow."""
    from custom_components.copilot_ha.config_flow import ConfigFlow

    flow = ConfigFlow.__new__(ConfigFlow)
    flow.hass = hass
    flow.context = {"entry_id": config_entry.entry_id}
    flow.source = "reauth"

    # Mock HA flow methods
    flow._async_current_entries = MagicMock(return_value=[config_entry])
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})

    # Mock config entry retrieval for reauth
    hass.config_entries.async_get_entry = MagicMock(return_value=config_entry)

    return flow


# ═══════════════════════════════════════════════════════════════════════════
# Options Flow Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_options_flow(hass: FakeHass, config_entry: FakeConfigEntry):
    """Build an OptionsFlowHandler instance with mocked HA methods.
    
    Returns an OptionsFlowHandler instance with all HA-specific methods mocked
    for isolated unit testing.
    """
    from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler

    flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
    flow._entry = config_entry
    flow._snapshot = None
    flow.hass = hass

    # Mock HA flow methods
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})

    return flow


@pytest.fixture
def options_flow_with_data(hass: FakeHass, config_entry_with_data: FakeConfigEntry):
    """Build an OptionsFlowHandler with pre-populated entry data."""
    from custom_components.copilot_ha.config_options_flow import OptionsFlowHandler

    flow = OptionsFlowHandler.__new__(OptionsFlowHandler)
    flow._entry = config_entry_with_data
    flow._snapshot = None
    flow.hass = hass

    # Mock HA flow methods
    flow.async_show_menu = MagicMock(return_value={"type": "menu"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_abort = MagicMock(return_value={"type": "abort"})

    return flow


# ═══════════════════════════════════════════════════════════════════════════
# Module/Registry Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_module():
    """Return a mock CopilotModule for testing."""
    mod = MagicMock()
    mod.name = "test_module"
    mod.async_setup_entry = AsyncMock()
    mod.async_unload_entry = AsyncMock(return_value=True)
    return mod


@pytest.fixture
def mock_failing_module():
    """Return a mock module that fails setup for error handling tests."""
    mod = MagicMock()
    mod.name = "failing_module"
    mod.async_setup_entry = AsyncMock(side_effect=RuntimeError("Setup failed"))
    mod.async_unload_entry = AsyncMock(return_value=True)
    return mod


@pytest.fixture
def module_registry():
    """Return a fresh ModuleRegistry instance."""
    from custom_components.copilot_ha.core.registry import ModuleRegistry
    return ModuleRegistry()


@pytest.fixture
def copilot_runtime(hass: FakeHass):
    """Return a CopilotRuntime singleton for the given hass."""
    from custom_components.copilot_ha.core.runtime import CopilotRuntime
    return CopilotRuntime.get(hass)


# ═══════════════════════════════════════════════════════════════════════════
# Patch Fixtures (Common mocking patterns)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def patch_discover_reachable():
    """Patch discover_reachable_core_endpoint to return a reachable endpoint."""
    with patch(
        "custom_components.copilot_ha.config_flow.discover_reachable_core_endpoint",
        new_callable=AsyncMock,
        return_value=("192.168.1.10", 8909),
    ) as mock:
        yield mock


@pytest.fixture
def patch_discover_unreachable():
    """Patch discover_reachable_core_endpoint to return None (unreachable)."""
    with patch(
        "custom_components.copilot_ha.config_flow.discover_reachable_core_endpoint",
        new_callable=AsyncMock,
        return_value=None,
    ) as mock:
        yield mock


@pytest.fixture
def patch_validate_input_success():
    """Patch validate_input to succeed."""
    with patch(
        "custom_components.copilot_ha.config_flow.validate_input",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def patch_validate_input_failure():
    """Patch validate_input to raise an exception."""
    with patch(
        "custom_components.copilot_ha.config_flow.validate_input",
        new_callable=AsyncMock,
        side_effect=Exception("Connection failed"),
    ) as mock:
        yield mock


@pytest.fixture
def patch_fetch_setup_token():
    """Patch fetch_setup_token to return a test token."""
    with patch(
        "custom_components.copilot_ha.config_flow.fetch_setup_token",
        new_callable=AsyncMock,
        return_value="auto_fetched_test_token",
    ) as mock:
        yield mock


# ═══════════════════════════════════════════════════════════════════════════
# Schema Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_connection_data():
    """Return sample connection configuration data."""
    return {
        "host": "192.168.1.100",
        "port": 8909,
        "token": "test_token",
        "assistant_name": "Styx",
        "entity_profile": "standard",
    }


@pytest.fixture
def sample_modules_data():
    """Return sample modules configuration data."""
    return {
        "watchdog_enabled": True,
        "events_forwarder_enabled": False,
        "waste_enabled": True,
        "birthday_enabled": False,
        "user_preference_enabled": True,
    }


@pytest.fixture
def sample_neuron_data():
    """Return sample neuron configuration data."""
    return {
        "neuron_enabled": True,
        "neuron_evaluation_interval": 60,
        "neuron_context_entities": ["sensor.temperature", "sensor.humidity"],
        "neuron_state_entities": [],
        "neuron_mood_entities": "sensor.mood1, sensor.mood2",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Async Event Loop Fixture (for pytest-asyncio)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════════════════════
# Marker Configuration
# ═══════════════════════════════════════════════════════════════════════════


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "config_flow: marks tests as ConfigFlow tests"
    )
    config.addinivalue_line(
        "markers", "options_flow: marks tests as OptionsFlow tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (no HA runtime required)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


# Backward-compatible aliases for older tests in this repository
ConfigEntry = FakeConfigEntry
MockHass = FakeHass
