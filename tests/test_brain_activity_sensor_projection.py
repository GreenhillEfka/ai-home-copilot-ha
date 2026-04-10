"""Projection contract tests for brain_activity_sensor.py (HA-313).

Verifies BrainActivitySensor is a pure projection shell on:
  - /api/v1/hub/brain/activity
  - coordinator.data["neurons_fired"]
  - coordinator.data["brain_insights"]

This slice hardens malformed recent_pulses / recent_chat / webhook payloads so
non-list or non-dict items cannot crash attribute projection.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class BrainActivitySensorContract:
    """Mirror of BrainActivitySensor projection logic."""

    _STATE_LABELS = {
        "active": "Aktiv — pulsierend",
        "idle": "Wach — bereit",
        "sleeping": "Schlafend",
    }

    _STATE_ICONS = {
        "active": "mdi:head-lightbulb",
        "idle": "mdi:brain",
        "sleeping": "mdi:power-sleep",
    }

    @staticmethod
    def _as_mapping(value) -> dict:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value) -> list:
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_string(value, default: str = "") -> str:
        return value if isinstance(value, str) else default

    @staticmethod
    def native_value(data: dict) -> str:
        state = data.get("state", "idle")
        return BrainActivitySensorContract._STATE_LABELS.get(state, state)

    @staticmethod
    def icon(data: dict) -> str:
        state = data.get("state", "idle")
        return BrainActivitySensorContract._STATE_ICONS.get(state, "mdi:brain")

    @staticmethod
    def extra_state_attributes(data: dict, coord_data: dict | None = None) -> dict:
        data = BrainActivitySensorContract._as_mapping(data)
        coord_data = BrainActivitySensorContract._as_mapping(coord_data)
        attrs: dict = {
            "state": data.get("state", "idle"),
            "total_pulses": data.get("total_pulses", 0),
            "total_chat_messages": data.get("total_chat_messages", 0),
            "uptime_seconds": data.get("uptime_seconds", 0),
            "sleep_seconds": data.get("sleep_seconds", 0),
            "idle_timeout_seconds": data.get("idle_timeout_seconds", 300),
            "sleep_timeout_seconds": data.get("sleep_timeout_seconds", 1800),
            "last_active": data.get("last_active", ""),
        }

        recent_pulses = BrainActivitySensorContract._as_list(data.get("recent_pulses", []))
        if recent_pulses:
            attrs["recent_pulses"] = [
                {"reason": pulse.get("reason"), "duration_ms": pulse.get("duration_ms")}
                for pulse in recent_pulses[:3]
                if isinstance(pulse, dict)
            ]

        recent_chat = BrainActivitySensorContract._as_list(data.get("recent_chat", []))
        if recent_chat:
            attrs["recent_chat"] = [
                {
                    "role": message.get("role"),
                    "content": BrainActivitySensorContract._as_string(message.get("content"))[:100],
                }
                for message in recent_chat[:3]
                if isinstance(message, dict)
            ]

        neurons_fired = BrainActivitySensorContract._as_list(coord_data.get("neurons_fired", []))
        attrs["neurons_fired_count"] = len(neurons_fired)
        if neurons_fired:
            last = BrainActivitySensorContract._as_mapping(neurons_fired[-1])
            attrs["last_neuron_fired"] = last.get("neuron_id", last.get("name", "unknown"))
            attrs["last_neuron_fired_at"] = last.get("fired_at", last.get("timestamp", ""))

        brain_insights = BrainActivitySensorContract._as_list(coord_data.get("brain_insights", []))
        attrs["brain_insights_count"] = len(brain_insights)
        if brain_insights:
            last_insight = BrainActivitySensorContract._as_mapping(brain_insights[-1])
            attrs["last_brain_insight"] = last_insight.get("insight_type", last_insight.get("type", "unknown"))
            attrs["last_brain_insight_summary"] = BrainActivitySensorContract._as_string(
                last_insight.get("summary", last_insight.get("description", ""))
            )[:200]

        return attrs


@pytest.mark.parametrize("raw_state,expected", [
    ("active", "Aktiv — pulsierend"),
    ("idle", "Wach — bereit"),
    ("sleeping", "Schlafend"),
    ("unknown", "unknown"),
    ("", ""),
])
def test_BA1_native_value(raw_state, expected):
    assert BrainActivitySensorContract.native_value({"state": raw_state}) == expected


@pytest.mark.parametrize("raw_state,expected_icon", [
    ("active", "mdi:head-lightbulb"),
    ("idle", "mdi:brain"),
    ("sleeping", "mdi:power-sleep"),
    ("unknown", "mdi:brain"),
    ("", "mdi:brain"),
])
def test_BA2_icon(raw_state, expected_icon):
    assert BrainActivitySensorContract.icon({"state": raw_state}) == expected_icon


def test_BA3_attrs_from_fetch():
    fetch_data = {
        "ok": True,
        "state": "active",
        "total_pulses": 42,
        "total_chat_messages": 7,
        "uptime_seconds": 3600,
        "sleep_seconds": 120,
        "idle_timeout_seconds": 300,
        "sleep_timeout_seconds": 1800,
        "last_active": "2026-04-05T12:00:00Z",
        "recent_pulses": [
            {"reason": "user_message", "duration_ms": 150},
            {"reason": "tool_call", "duration_ms": 80},
        ],
        "recent_chat": [
            {"role": "user", "content": "Wie wird das Wetter?"},
            {"role": "assistant", "content": "Sonnig bei 22 Grad."},
        ],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes(fetch_data, {})
    assert attrs["state"] == "active"
    assert attrs["total_pulses"] == 42
    assert attrs["total_chat_messages"] == 7
    assert attrs["uptime_seconds"] == 3600
    assert attrs["sleep_seconds"] == 120
    assert attrs["recent_pulses"][0] == {"reason": "user_message", "duration_ms": 150}
    assert attrs["recent_chat"][0] == {"role": "user", "content": "Wie wird das Wetter?"}


def test_BA4_attrs_from_coordinator_neurons():
    coord_data = {
        "neurons_fired": [
            {"neuron_id": "habitus_learning", "name": "HabitusLearner", "fired_at": "2026-04-05T12:00:00Z"},
            {"neuron_id": "memory_consolidation", "name": "MemoryNeuron", "fired_at": "2026-04-05T12:02:00Z"},
        ],
        "brain_insights": [],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)
    assert attrs["neurons_fired_count"] == 2
    assert attrs["last_neuron_fired"] == "memory_consolidation"
    assert attrs["last_neuron_fired_at"] == "2026-04-05T12:02:00Z"


def test_BA5_attrs_from_coordinator_insights():
    coord_data = {
        "neurons_fired": [],
        "brain_insights": [
            {"insight_type": "pattern_detected", "summary": "User prefers morning automation"},
            {"insight_type": "habit_learned", "summary": "Evening routine established"},
        ],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)
    assert attrs["brain_insights_count"] == 2
    assert attrs["last_brain_insight"] == "habit_learned"
    assert attrs["last_brain_insight_summary"] == "Evening routine established"


def test_BA6_edge_missing_state_key():
    assert BrainActivitySensorContract.native_value({}) == "Wach — bereit"
    assert BrainActivitySensorContract.icon({}) == "mdi:brain"


def test_BA7_edge_empty_coordinator_data():
    attrs = BrainActivitySensorContract.extra_state_attributes({}, {})
    assert attrs["neurons_fired_count"] == 0
    assert attrs["brain_insights_count"] == 0


def test_BA8_edge_recent_pulses_capped():
    data = {"recent_pulses": [{"reason": f"r{i}", "duration_ms": i * 10} for i in range(10)]}
    attrs = BrainActivitySensorContract.extra_state_attributes(data, {})
    assert len(attrs["recent_pulses"]) == 3


def test_BA9_edge_recent_chat_truncated():
    data = {"recent_chat": [{"role": "user", "content": "A" * 200}]}
    attrs = BrainActivitySensorContract.extra_state_attributes(data, {})
    assert len(attrs["recent_chat"][0]["content"]) == 100


@pytest.mark.parametrize("payload,key", [
    ({"recent_pulses": "not-a-list"}, "recent_pulses"),
    ({"recent_chat": "not-a-list"}, "recent_chat"),
])
def test_BA10_non_list_fetch_payloads_do_not_project(payload, key):
    attrs = BrainActivitySensorContract.extra_state_attributes(payload, {})
    assert key not in attrs


def test_BA11_non_dict_fetch_items_are_filtered():
    data = {
        "recent_pulses": ["bad", {"reason": "tool_call", "duration_ms": 80}, None],
        "recent_chat": [42, {"role": "assistant", "content": None}],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes(data, {})
    assert attrs["recent_pulses"] == [{"reason": "tool_call", "duration_ms": 80}]
    assert attrs["recent_chat"] == [{"role": "assistant", "content": ""}]


@pytest.mark.parametrize("coord_data,count_key", [
    ({"neurons_fired": "bad"}, "neurons_fired_count"),
    ({"brain_insights": {"bad": True}}, "brain_insights_count"),
])
def test_BA12_non_list_webhook_payloads_fall_back_to_zero(coord_data, count_key):
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)
    assert attrs[count_key] == 0


def test_BA13_non_dict_last_webhook_items_fall_back_safely():
    coord_data = {
        "neurons_fired": [{"neuron_id": "n1", "fired_at": "2026-04-05T12:00:00Z"}, "bad"],
        "brain_insights": [{"insight_type": "pattern_detected", "summary": "ok"}, None],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)
    assert attrs["neurons_fired_count"] == 2
    assert attrs["last_neuron_fired"] == "unknown"
    assert attrs["last_neuron_fired_at"] == ""
    assert attrs["brain_insights_count"] == 2
    assert attrs["last_brain_insight"] == "unknown"
    assert attrs["last_brain_insight_summary"] == ""


@pytest.mark.parametrize("raw_state", ["active", "idle", "sleeping"])
def test_GC1_pure_projection_no_local_semantics(raw_state):
    nv = BrainActivitySensorContract.native_value({"state": raw_state})
    assert nv in ("Aktiv — pulsierend", "Wach — bereit", "Schlafend")


def test_GC2_endpoint_contract():
    attrs = BrainActivitySensorContract.extra_state_attributes(
        {"state": "idle", "total_pulses": 10},
        {"neurons_fired": [{"neuron_id": "n1"}], "brain_insights": []},
    )
    assert attrs["total_pulses"] == 10
    assert attrs["neurons_fired_count"] == 1


def test_GC3_source_guards_present():
    source = Path("custom_components/pilotsuite/sensors/brain_activity_sensor.py").read_text()
    assert "def _as_mapping(value: Any) -> dict[str, Any]:" in source
    assert "def _as_list(value: Any) -> list[Any]:" in source
    assert 'recent_pulses = _as_list(data.get("recent_pulses", []))' in source
    assert 'recent_chat = _as_list(data.get("recent_chat", []))' in source
    assert 'coord_data = _as_mapping(self.coordinator.data)' in source
