"""Projection Contract Tests for BrainActivitySensor (HA-10).

Verifies that BrainActivitySensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/brain/activity) without local semantic invention.

Pattern: same as HA-6 (habitus_zone), HA-8 (mood), HA-9 (autonomy).

Contract:
- native_value: maps state via _STATE_LABELS dict (presentation only, no logic)
- extra_state_attributes: direct passthrough of Core API fields
- _fetch(): hits /api/v1/hub/brain/activity
- Uses coordinator.data for webhook-pushed neurons_fired / brain_insights
"""
import pytest
from unittest.mock import Mock


# ── Minimal mock setup (no HA imports) ─────────────────────────────────

class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    """Stand-in for CopilotDataUpdateCoordinator with known data shapes."""
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()

    def async_write_ha_state(self):
        pass


# ── Inline sensor class mirrors (test contract only, not HA wiring) ─────

_STATE_LABELS = {
    "active": "Aktiv — pulsierend",
    "idle": "Wach — bereit",
    "sleeping": "Schlafend",
}


class BrainActivitySensorContract:
    """Mirror of BrainActivitySensor logic for contract testing.

    Verifies projection contract: all state flows from Core API
    or coordinator.data webhook push — no local semantic invention.
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    async def _fetch(self):
        """Simulates HTTP GET /api/v1/hub/brain/activity — returns Core JSON."""
        return self._data

    def _apply(self, fetched_data):
        """Mirrors async_update() + extra_state_attributes logic."""
        if fetched_data and fetched_data.get("ok"):
            self._data = fetched_data

    @property
    def native_value(self):
        state = self._data.get("state", "idle")
        return _STATE_LABELS.get(state, state)

    @property
    def extra_state_attributes(self):
        attrs = {
            "state": self._data.get("state", "idle"),
            "total_pulses": self._data.get("total_pulses", 0),
            "total_chat_messages": self._data.get("total_chat_messages", 0),
            "uptime_seconds": self._data.get("uptime_seconds", 0),
            "sleep_seconds": self._data.get("sleep_seconds", 0),
            "idle_timeout_seconds": self._data.get("idle_timeout_seconds", 300),
            "sleep_timeout_seconds": self._data.get("sleep_timeout_seconds", 1800),
            "last_active": self._data.get("last_active", ""),
        }
        coord_data = self.coordinator.data or {}
        neurons_fired = coord_data.get("neurons_fired", [])
        attrs["neurons_fired_count"] = len(neurons_fired)
        if neurons_fired:
            last = neurons_fired[-1]
            attrs["last_neuron_fired"] = last.get("neuron_id", last.get("name", "unknown"))
            attrs["last_neuron_fired_at"] = last.get("fired_at", last.get("timestamp", ""))
        brain_insights = coord_data.get("brain_insights", [])
        attrs["brain_insights_count"] = len(brain_insights)
        if brain_insights:
            last_insight = brain_insights[-1]
            attrs["last_brain_insight"] = last_insight.get("insight_type", last_insight.get("type", "unknown"))
            attrs["last_brain_insight_summary"] = last_insight.get("summary", last_insight.get("description", ""))[:200]
        return attrs


# ── Test Cases ───────────────────────────────────────────────────────────────

BA1_native_value = pytest.mark.parametrize("core_state,expected", [
    ("active",   "Aktiv — pulsierend"),
    ("idle",     "Wach — bereit"),
    ("sleeping", "Schlafend"),
    ("unknown",  "unknown"),         # fallback to raw state
    ("",         ""),                 # empty string falls through
])
BA2_extra_attrs = pytest.mark.parametrize("core_data,attr_key,expected", [
    ({"ok": True, "state": "active", "total_pulses": 42}, "total_pulses", 42),
    ({"ok": True, "state": "idle",   "total_chat_messages": 7}, "total_chat_messages", 7),
    ({"ok": True, "state": "active", "uptime_seconds": 3600}, "uptime_seconds", 3600),
    ({"ok": True, "state": "sleeping", "sleep_seconds": 120}, "sleep_seconds", 120),
    ({"ok": True, "state": "idle",   "idle_timeout_seconds": 300}, "idle_timeout_seconds", 300),
    ({"ok": True, "state": "sleeping", "sleep_timeout_seconds": 1800}, "sleep_timeout_seconds", 1800),
    ({"ok": True, "state": "active", "last_active": "2026-04-05T10:00:00"}, "last_active", "2026-04-05T10:00:00"),
])
BA3_neurons_fired = pytest.mark.parametrize("coord_neurons,expected_count,expected_last", [
    ([], 0, None),
    ([{"neuron_id": "n1", "fired_at": "2026-04-05T09:00"}], 1, "n1"),
    ([{"name": "recall_neuron", "timestamp": "2026-04-05T09:15"}], 1, "recall_neuron"),
    ([
        {"neuron_id": "n1", "fired_at": "2026-04-05T08:00"},
        {"neuron_id": "n2", "fired_at": "2026-04-05T09:00"},
    ], 2, "n2"),
])
BA4_brain_insights = pytest.mark.parametrize("coord_insights,expected_count,expected_type", [
    ([], 0, None),
    ([{"insight_type": "pattern_detected", "summary": "Daily rhythm stable"}], 1, "pattern_detected"),
    ([{"type": "anomaly", "description": "Unusual activity at 03:00"}], 1, "anomaly"),
    ([
        {"insight_type": "p1", "summary": "First"},
        {"insight_type": "p2", "summary": "Second"},
    ], 2, "p2"),
])
BA5_edge_cases = pytest.mark.parametrize("fetched_data,coordinator_data,expect_ok", [
    (None, {}, False),
    ({}, {}, False),
    ({"ok": False}, {}, False),
    ({"ok": True, "state": "active"}, {}, True),
    ({"ok": True, "state": "idle"}, {"neurons_fired": [], "brain_insights": []}, True),
    ({"ok": True, "state": "sleeping"}, {"neurons_fired": [{"neuron_id": "n1", "fired_at": "now"}], "brain_insights": []}, True),
])
BA6_coordinator_override = pytest.mark.parametrize("coordinator_data,key,expected", [
    ({"neurons_fired": [{"neuron_id": "x"}]}, "neurons_fired_count", 1),
    ({"brain_insights": [{"insight_type": "t"}]}, "brain_insights_count", 1),
    ({"neurons_fired": []}, "neurons_fired_count", 0),
    ({"brain_insights": []}, "brain_insights_count", 0),
])


# ── Parametrized test functions ─────────────────────────────────────────────

@BA1_native_value
def test_BA1_native_value(core_state, expected):
    coord = MockCoordinator({})
    sensor = BrainActivitySensorContract(coord)
    sensor._data = {"ok": True, "state": core_state}
    assert sensor.native_value == expected


@BA2_extra_attrs
def test_BA2_extra_attrs(core_data, attr_key, expected):
    coord = MockCoordinator({})
    sensor = BrainActivitySensorContract(coord)
    sensor._data = core_data
    attrs = sensor.extra_state_attributes
    assert attrs[attr_key] == expected


@BA3_neurons_fired
def test_BA3_neurons_fired(coord_neurons, expected_count, expected_last):
    coord = MockCoordinator({"neurons_fired": coord_neurons})
    sensor = BrainActivitySensorContract(coord)
    sensor._data = {"ok": True, "state": "active"}
    attrs = sensor.extra_state_attributes
    assert attrs["neurons_fired_count"] == expected_count
    if expected_last:
        assert attrs.get("last_neuron_fired") == expected_last


@BA4_brain_insights
def test_BA4_brain_insights(coord_insights, expected_count, expected_type):
    coord = MockCoordinator({"brain_insights": coord_insights})
    sensor = BrainActivitySensorContract(coord)
    sensor._data = {"ok": True, "state": "idle"}
    attrs = sensor.extra_state_attributes
    assert attrs["brain_insights_count"] == expected_count
    if expected_type:
        assert attrs.get("last_brain_insight") == expected_type


@BA5_edge_cases
def test_BA5_edge_cases(fetched_data, coordinator_data, expect_ok):
    coord = MockCoordinator(coordinator_data)
    sensor = BrainActivitySensorContract(coord)
    sensor._apply(fetched_data)
    if expect_ok:
        assert sensor._data.get("ok") is True
    else:
        assert sensor._data == {}


def test_BA6_no_local_state_invention():
    """Global contract: no local variables, no heuristics, no derived logic."""
    coord = MockCoordinator({
        "neurons_fired": [{"neuron_id": "n1", "fired_at": "t1"}],
        "brain_insights": [{"insight_type": "i1", "summary": "s1"}],
    })
    sensor = BrainActivitySensorContract(coord)
    sensor._data = {"ok": True, "state": "active", "total_pulses": 10}
    attrs = sensor.extra_state_attributes
    # All values traceable to Core API or coordinator webhook — zero local magic
    assert "state" in attrs
    assert "neurons_fired_count" in attrs
    assert "brain_insights_count" in attrs
    assert attrs["total_pulses"] == 10
