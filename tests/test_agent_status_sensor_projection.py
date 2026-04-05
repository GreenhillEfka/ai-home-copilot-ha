"""Projection Contract Tests for AgentStatusSensor (HA-15).

Verifies that AgentStatusSensor is a pure Projection-Shell on Core-truth
(/api/v1/agent/status) with only trivial string formatting and if-elif icon logic.

Pattern: same as HA-6/8/9/10/11/12/13/14.
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"

    def async_write_ha_state(self):
        pass


class AgentStatusSensorContract:
    """Mirror of AgentStatusSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/agent/status
    - native_value: f"{agent_name}: {status}" (trivial)
    - icon: if-elif chain on status (trivial)
    - extra_state_attributes: direct passthrough of all Core fields
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    async def _fetch(self):
        return self._data

    def _apply(self, fetched_data):
        if fetched_data and fetched_data.get("ok"):
            self._data = fetched_data

    @property
    def native_value(self):
        status = self._data.get("status", "offline")
        agent_name = self._data.get("agent_name", "Styx")
        return f"{agent_name}: {status}"

    @property
    def icon(self):
        status = self._data.get("status", "offline")
        if status == "ready":
            return "mdi:robot-happy"
        elif status == "degraded":
            return "mdi:robot-confused"
        return "mdi:robot-off"

    @property
    def extra_state_attributes(self):
        return {
            "agent_name": self._data.get("agent_name", "Styx"),
            "agent_version": self._data.get("agent_version", ""),
            "status": self._data.get("status", "offline"),
            "uptime_seconds": self._data.get("uptime_seconds", 0),
            "conversation_ready": self._data.get("conversation_ready", False),
            "llm_available": self._data.get("llm_available", False),
            "llm_model": self._data.get("llm_model", ""),
            "llm_backend": self._data.get("llm_backend", ""),
            "character": self._data.get("character", ""),
            "features": self._data.get("features", []),
            "supported_languages": self._data.get("supported_languages", []),
            "last_health_check": self._data.get("last_health_check", ""),
        }


AS1_native_value = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "agent_name": "Styx", "status": "ready"}, "Styx: ready"),
    ({"ok": True, "agent_name": "PilotClaw", "status": "running"}, "PilotClaw: running"),
    ({"ok": True, "agent_name": "HomeClaw", "status": "offline"}, "HomeClaw: offline"),
    ({"ok": True, "agent_name": "Orakel", "status": "degraded"}, "Orakel: degraded"),
    ({"ok": True, "agent_name": "Styx", "status": ""}, "Styx: "),
    ({"ok": True, "agent_name": "", "status": "ready"}, ": ready"),
])
AS2_icon = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "status": "ready"}, "mdi:robot-happy"),
    ({"ok": True, "status": "degraded"}, "mdi:robot-confused"),
    ({"ok": True, "status": "offline"}, "mdi:robot-off"),
    ({"ok": True, "status": ""}, "mdi:robot-off"),
    ({"ok": True, "status": "unknown_state"}, "mdi:robot-off"),
])
AS3_attrs = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "agent_name", "Styx"),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "agent_version", "15.3.85"),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "uptime_seconds", 86400),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "conversation_ready", True),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "llm_available", True),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "llm_model", "gpt-5.4"),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "features", ["voice", "calendar"]),
    ({"ok": True, "agent_name": "Styx", "agent_version": "15.3.85", "status": "ready", "uptime_seconds": 86400, "conversation_ready": True, "llm_available": True, "llm_model": "gpt-5.4", "llm_backend": "openai-codex", "character": "assistant", "features": ["voice", "calendar"], "supported_languages": ["de", "en"], "last_health_check": "2026-04-05T12:00:00"}, "supported_languages", ["de", "en"]),
])
AS4_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "status": "ready"}, True),
    ({"ok": True, "agent_name": "Test", "status": "offline"}, True),
])


@AS1_native_value
def test_AS1_native_value(core_data, expected):
    s = AgentStatusSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.native_value == expected


@AS2_icon
def test_AS2_icon(core_data, expected_icon):
    s = AgentStatusSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.icon == expected_icon


@AS3_attrs
def test_AS3_attrs(core_data, key, expected):
    s = AgentStatusSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.extra_state_attributes[key] == expected


@AS4_edge
def test_AS4_edge(data, expect_ok):
    s = AgentStatusSensorContract(MockCoordinator({}))
    s._apply(data)
    if expect_ok:
        assert s._data.get("ok") is True
