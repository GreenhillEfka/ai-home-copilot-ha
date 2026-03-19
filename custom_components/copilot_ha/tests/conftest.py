"""Shared test fixtures for PilotSuite ConfigFlow/OptionsFlow/SnapshotFlow tests.

Provides:
- _FakeConfigEntry: lightweight config entry stub
- _FakeHass: minimal hass stub for tests needing hass.data / hass.config
- async_flow_hass: pytest fixture for async flow tests
- config_entry_factory: factory fixture for creating test entries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest


@dataclass
class _FakeConfigEntry:
    """Lightweight ConfigEntry stub for unit tests."""
    entry_id: str = "test_entry_1"
    domain: str = "copilot_ha"
    title: str = "PilotSuite Test"
    data: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)
    unique_id: str | None = None
    version: int = 1
    minor_version: int = 0
    source: str = "user"
    state: int = 1  # ConfigEntryState.LOADED

    def __post_init__(self):
        if not self.data:
            self.data = {"host": "127.0.0.1", "port": 8909, "token": "test-token"}
        if not self.options:
            self.options = {}


@dataclass
class _FakeConfigEntryOptions:
    """ConfigEntry with custom options for OptionsFlow tests."""
    entry_id: str = "test_entry_1"
    domain: str = "copilot_ha"
    title: str = "PilotSuite Test"
    data: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.data:
            self.data = {"host": "192.168.1.10", "port": 8909, "token": "test-token"}
        if not self.options:
            self.options = {
                "global_automation_mode": "learning",
                "zone_automation_modes": {},
            }


class _FakeHass:
    """Minimal hass stub for tests that need hass.data / hass.config."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self.config = MagicMock()
        self.config.internal_url = None
        self.config.external_url = None
        self.async_add_executor_job = lambda fn, *args: fn(*args)
        self.config_entries = MagicMock()
        self.config_entries.async_update_entry = MagicMock()
        self.config_entries.async_reload = MagicMock()


@pytest.fixture
def async_flow_hass() -> _FakeHass:
    """Provide a lightweight hass instance for async flow tests."""
    return _FakeHass()


@pytest.fixture
def config_entry_factory() -> callable:
    """Factory fixture for creating test config entries."""
    def _factory(
        entry_id: str = "test_entry",
        data: dict | None = None,
        options: dict | None = None,
    ) -> _FakeConfigEntry:
        return _FakeConfigEntry(
            entry_id=entry_id,
            data=data or {},
            options=options or {},
        )
    return _factory


@pytest.fixture
def config_entry_with_options(config_entry_factory: callable) -> _FakeConfigEntry:
    """ConfigEntry with typical options for OptionsFlow tests."""
    return config_entry_factory(
        entry_id="test_entry_options",
        data={"host": "192.168.1.10", "port": 8909, "token": "test-token"},
        options={
            "global_automation_mode": "learning",
            "zone_automation_modes": {},
        },
    )
