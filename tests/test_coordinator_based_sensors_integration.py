"""Integration Contract Tests for Coordinator-based Sensors (HA-45).

These sensors read from coordinator.data (filled by CopilotDataUpdateCoordinator).
They are NOT pure projection shells — the data transformation happens at the
coordinator level. Tests verify the sensor correctly reflects coordinator.data.

Covers: PredictiveAutomationSensor, InspectorSensor, NeuronDashboardSensor
Pattern: verify state/attributes correctly mirror coordinator.data passthrough.
"""
import pytest
from unittest.mock import Mock


class MockCoordinator:
    """Simulates CopilotDataUpdateCoordinator with pre-filled data."""
    def __init__(self, data=None):
        self.data = data or {}
        self.config_entry = Mock()
        self.config_entry.entry_id = "test_entry"
        self._hass = Mock()
        self._hass.data = {}

    def async_write_ha_state(self):
        pass


# ── PredictiveAutomationSensor contract ────────────────────────────────────

class PredictiveAutomationSensorContract:
    """Mirrors PredictiveAutomationSensor — reads count from coordinator.data['suggestions']."""
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def native_value(self):
        if not self.coordinator.data:
            return "idle"
        suggestions = self.coordinator.data.get("suggestions", [])
        return str(len(suggestions))

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        suggestions = self.coordinator.data.get("suggestions", [])
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "last_update": self.coordinator.data.get("last_update"),
        }


class PredictiveAutomationDetailsSensorContract:
    """Mirrors the details variant — top suggestion as state."""
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def native_value(self):
        if not self.coordinator.data:
            return "idle"
        suggestions = self.coordinator.data.get("suggestions", [])
        if not suggestions:
            return "idle"
        top = suggestions[0]
        return f"{top.get('type', 'unknown')} — {top.get('title', 'N/A')}"

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        suggestions = self.coordinator.data.get("suggestions", [])
        return {
            "top_type": suggestions[0].get("type") if suggestions else None,
            "top_confidence": suggestions[0].get("confidence") if suggestions else None,
        }


# ── InspectorSensor contract ───────────────────────────────────────────────

class InspectorSensorContract:
    """Mirrors InspectorSensor — reads zone/tag/character/mood counts from coordinator.data."""
    CONTRACT_TYPES = {
        "zones": ("zones", "zones"),
        "tags": ("tags", "tags"),
        "character": ("character", "profile"),
        "mood": ("mood", "current"),
    }

    def __init__(self, coordinator, sensor_type):
        self.coordinator = coordinator
        self._sensor_type = sensor_type

    @property
    def state(self):
        if not self.coordinator.data:
            return "unknown"
        data = self.coordinator.data
        key, subkey = self.CONTRACT_TYPES.get(self._sensor_type, (None, None))
        if key is None:
            return "unknown"
        section = data.get(key, {})
        if self._sensor_type in ("zones", "tags"):
            return len(section.get(subkey, []))
        return section.get(subkey, "unknown")


# ── NeuronDashboardSensor contract ──────────────────────────────────────

class NeuronDashboardSensorContract:
    """Mirrors NeuronDashboardSensor — mirrors coordinator.data['neurons']."""
    def __init__(self, coordinator):
        self.coordinator = coordinator

    @property
    def native_value(self):
        return "ok" if self.coordinator.data else "no_data"

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        neurons = self.coordinator.data.get("neurons", {})
        mood = self.coordinator.data.get("dominant_mood", "unknown")
        confidence = self.coordinator.data.get("mood_confidence", 0.0)
        return {
            "neuron_count": len(neurons),
            "neurons": neurons,
            "dominant_mood": mood,
            "mood_confidence": confidence,
        }


# ── Tests: PredictiveAutomationSensor ──────────────────────────────────────

def test_PA1_idle_no_data():
    c = MockCoordinator({})
    s = PredictiveAutomationSensorContract(c)
    assert s.native_value == "idle"

def test_PA2_count_from_suggestions():
    c = MockCoordinator({"suggestions": [{"id": 1}, {"id": 2}, {"id": 3}], "last_update": "2026-04-05T10:00:00Z"})
    s = PredictiveAutomationSensorContract(c)
    assert s.native_value == "3"
    attrs = s.extra_state_attributes
    assert attrs["count"] == 3
    assert attrs["last_update"] == "2026-04-05T10:00:00Z"

def test_PA3_empty_suggestions():
    c = MockCoordinator({"suggestions": []})
    s = PredictiveAutomationSensorContract(c)
    assert s.native_value == "0"

def test_PA4_details_top():
    c = MockCoordinator({"suggestions": [{"type": "presence", "title": "Lichtszene vorschlagen", "confidence": 0.92}]})
    s = PredictiveAutomationDetailsSensorContract(c)
    assert s.native_value == "presence — Lichtszene vorschlagen"
    attrs = s.extra_state_attributes
    assert attrs["top_type"] == "presence"
    assert attrs["top_confidence"] == 0.92


# ── Tests: InspectorSensor ────────────────────────────────────────────────

def test_INS1_zones_count():
    c = MockCoordinator({"zones": {"zones": [{"id": "z1"}, {"id": "z2"}]}})
    s = InspectorSensorContract(c, "zones")
    assert s.state == 2

def test_INS2_tags_count():
    c = MockCoordinator({"tags": {"tags": [{"id": "t1"}]}})
    s = InspectorSensorContract(c, "tags")
    assert s.state == 1

def test_INS3_character():
    c = MockCoordinator({"character": {"profile": "energetic"}})
    s = InspectorSensorContract(c, "character")
    assert s.state == "energetic"

def test_INS4_mood():
    c = MockCoordinator({"mood": {"current": "focused"}})
    s = InspectorSensorContract(c, "mood")
    assert s.state == "focused"

def test_INS5_unknown_no_data():
    c = MockCoordinator({})
    for stype in ("zones", "tags", "character", "mood"):
        s = InspectorSensorContract(c, stype)
        assert s.state == "unknown"


# ── Tests: NeuronDashboardSensor ─────────────────────────────────────────

def test_ND1_native_value_ok():
    c = MockCoordinator({"neurons": {"n1": {}, "n2": {}}, "dominant_mood": "calm", "mood_confidence": 0.88})
    s = NeuronDashboardSensorContract(c)
    assert s.native_value == "ok"

def test_ND2_native_value_no_data():
    c = MockCoordinator({})
    s = NeuronDashboardSensorContract(c)
    assert s.native_value == "no_data"

def test_ND3_attrs():
    c = MockCoordinator({"neurons": {"presence": {"state": "active"}, "light": {"state": "on"}}, "dominant_mood": "calm", "mood_confidence": 0.88})
    s = NeuronDashboardSensorContract(c)
    attrs = s.extra_state_attributes
    assert attrs["neuron_count"] == 2
    assert attrs["dominant_mood"] == "calm"
    assert attrs["mood_confidence"] == 0.88
    assert "presence" in attrs["neurons"]
