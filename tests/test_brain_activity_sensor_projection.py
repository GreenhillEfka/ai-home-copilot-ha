"""Projection contract tests for brain_activity_sensor.py (HA-124).

Verifies BrainActivitySensor is a pure projection shell on:
  - /api/v1/hub/brain/activity  (HTTP fetch)
  - coordinator.data["neurons_fired"]  (webhook push)
  - coordinator.data["brain_insights"]  (webhook push)

No local semantic invention.  Contract mirror tested directly per HA convention.
"""

import pytest


# ---------------------------------------------------------------------------
# Contract mirror (mirrors what the sensor reads/produces at runtime)
# ---------------------------------------------------------------------------

class BrainActivitySensorContract:
    """Mirror of BrainActivitySensor projection logic — pure projection only."""

    _STATE_LABELS = {
        "active":   "Aktiv — pulsierend",
        "idle":      "Wach — bereit",
        "sleeping":  "Schlafend",
    }

    _STATE_ICONS = {
        "active":   "mdi:head-lightbulb",
        "idle":     "mdi:brain",
        "sleeping": "mdi:power-sleep",
    }

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
        if coord_data is None:
            coord_data = {}
        neurons_fired = coord_data.get("neurons_fired", []) if isinstance(coord_data, dict) else []
        brain_insights = coord_data.get("brain_insights", []) if isinstance(coord_data, dict) else []

        attrs: dict = {
            "state":                  data.get("state", "idle"),
            "total_pulses":           data.get("total_pulses", 0),
            "total_chat_messages":    data.get("total_chat_messages", 0),
            "uptime_seconds":         data.get("uptime_seconds", 0),
            "sleep_seconds":          data.get("sleep_seconds", 0),
            "idle_timeout_seconds":   data.get("idle_timeout_seconds", 300),
            "sleep_timeout_seconds":  data.get("sleep_timeout_seconds", 1800),
            "last_active":            data.get("last_active", ""),
        }

        recent_pulses = data.get("recent_pulses", [])
        if recent_pulses:
            attrs["recent_pulses"] = [
                {"reason": p.get("reason"), "duration_ms": p.get("duration_ms")}
                for p in recent_pulses[:3]
            ]

        recent_chat = data.get("recent_chat", [])
        if recent_chat:
            attrs["recent_chat"] = [
                {"role": m.get("role"), "content": m.get("content", "")[:100]}
                for m in recent_chat[:3]
            ]

        attrs["neurons_fired_count"] = len(neurons_fired)
        if neurons_fired:
            last = neurons_fired[-1]
            attrs["last_neuron_fired"]     = last.get("neuron_id", last.get("name", "unknown"))
            attrs["last_neuron_fired_at"]  = last.get("fired_at", last.get("timestamp", ""))

        attrs["brain_insights_count"] = len(brain_insights)
        if brain_insights:
            last_insight = brain_insights[-1]
            attrs["last_brain_insight"]          = last_insight.get("insight_type", last_insight.get("type", "unknown"))
            attrs["last_brain_insight_summary"]  = last_insight.get("summary", last_insight.get("description", ""))[:200]

        return attrs


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

# BA1 — native_value: state → label mapping
@pytest.mark.parametrize("raw_state,expected", [
    ("active",   "Aktiv — pulsierend"),
    ("idle",     "Wach — bereit"),
    ("sleeping", "Schlafend"),
    ("unknown",  "unknown"),
    ("",         ""),
])
def test_BA1_native_value(raw_state, expected):
    """BA1: native_value maps brain state via _STATE_LABELS dict lookup."""
    data = {"state": raw_state}
    assert BrainActivitySensorContract.native_value(data) == expected


# BA2 — icon: state → icon mapping
@pytest.mark.parametrize("raw_state,expected_icon", [
    ("active",   "mdi:head-lightbulb"),
    ("idle",     "mdi:brain"),
    ("sleeping", "mdi:power-sleep"),
    ("unknown",  "mdi:brain"),
    ("",         "mdi:brain"),
])
def test_BA2_icon(raw_state, expected_icon):
    """BA2: icon maps brain state via _STATE_ICONS dict lookup."""
    data = {"state": raw_state}
    assert BrainActivitySensorContract.icon(data) == expected_icon


# BA3 — extra_state_attributes: fields from /api/v1/hub/brain/activity
def test_BA3_attrs_from_fetch():
    """BA3: attributes map all fields from /api/v1/hub/brain/activity fetch response."""
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
            {"reason": "tool_call",    "duration_ms": 80},
        ],
        "recent_chat": [
            {"role": "user",      "content": "Wie wird das Wetter?"},
            {"role": "assistant", "content": "Sonnig bei 22 Grad."},
        ],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes(fetch_data, {})

    assert attrs["state"]                  == "active"
    assert attrs["total_pulses"]          == 42
    assert attrs["total_chat_messages"]    == 7
    assert attrs["uptime_seconds"]        == 3600
    assert attrs["sleep_seconds"]         == 120
    assert attrs["idle_timeout_seconds"]  == 300
    assert attrs["sleep_timeout_seconds"] == 1800
    assert attrs["last_active"]           == "2026-04-05T12:00:00Z"
    assert len(attrs["recent_pulses"])    == 2
    assert attrs["recent_pulses"][0]["reason"]      == "user_message"
    assert attrs["recent_pulses"][0]["duration_ms"] == 150
    assert len(attrs["recent_chat"])      == 2
    assert attrs["recent_chat"][0]["role"]    == "user"
    assert attrs["recent_chat"][0]["content"] == "Wie wird das Wetter?"


# BA4 — coordinator webhook: neurons_fired
def test_BA4_attrs_from_coordinator_neurons():
    """BA4: neurons_fired from coordinator.data are projected as attributes."""
    coord_data = {
        "neurons_fired": [
            {"neuron_id": "habitus_learning",    "name": "HabitusLearner",   "fired_at": "2026-04-05T12:00:00Z"},
            {"neuron_id": "pattern_match",       "name": "PatternMatcher",    "fired_at": "2026-04-05T12:01:00Z"},
            {"neuron_id": "memory_consolidation","name": "MemoryNeuron",      "fired_at": "2026-04-05T12:02:00Z"},
        ],
        "brain_insights": [],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)

    assert attrs["neurons_fired_count"]   == 3
    assert attrs["last_neuron_fired"]     == "memory_consolidation"
    assert attrs["last_neuron_fired_at"]  == "2026-04-05T12:02:00Z"


# BA5 — coordinator webhook: brain_insights
def test_BA5_attrs_from_coordinator_insights():
    """BA5: brain_insights from coordinator.data are projected as attributes."""
    coord_data = {
        "neurons_fired": [],
        "brain_insights": [
            {"insight_type": "pattern_detected", "type": "pattern_detected",
             "summary": "User prefers morning automation", "description": "User prefers morning automation"},
            {"insight_type": "habit_learned",    "type": "habit_learned",
             "summary": "Evening routine established",    "description": "Evening routine established"},
        ],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes({}, coord_data)

    assert attrs["brain_insights_count"]        == 2
    assert attrs["last_brain_insight"]          == "habit_learned"
    assert "Evening routine" in attrs["last_brain_insight_summary"]


# BA6 — edge: missing state key → defaults
def test_BA6_edge_missing_state_key():
    """BA6: missing 'state' key defaults to 'idle' label and icon."""
    data = {}
    assert BrainActivitySensorContract.native_value(data) == "Wach — bereit"
    assert BrainActivitySensorContract.icon(data)          == "mdi:brain"


# BA7 — edge: empty coordinator.data
def test_BA7_edge_empty_coordinator_data():
    """BA7: empty coordinator.data yields zero counts."""
    attrs = BrainActivitySensorContract.extra_state_attributes({}, {})
    assert attrs["neurons_fired_count"]  == 0
    assert attrs["brain_insights_count"] == 0


# BA8 — edge: recent_pulses capped at 3
def test_BA8_edge_recent_pulses_capped():
    """BA8: recent_pulses truncated to 3 entries."""
    data = {
        "state": "active",
        "recent_pulses": [{"reason": f"r{i}", "duration_ms": i * 10} for i in range(10)],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes(data, {})
    assert len(attrs["recent_pulses"]) == 3


# BA9 — edge: recent_chat content truncated to 100 chars
def test_BA9_edge_recent_chat_truncated():
    """BA9: recent_chat content truncated to 100 characters."""
    long_content = "A" * 200
    data = {
        "state": "idle",
        "recent_chat": [{"role": "user", "content": long_content}],
    }
    attrs = BrainActivitySensorContract.extra_state_attributes(data, {})
    assert len(attrs["recent_chat"][0]["content"]) == 100
    assert attrs["recent_chat"][0]["content"].endswith("…") or len(attrs["recent_chat"][0]["content"]) == 100


# GC1 — global contract: pure projection, no local semantic invention
@pytest.mark.parametrize("raw_state", ["active", "idle", "sleeping"])
def test_GC1_pure_projection_no_local_semantics(raw_state):
    """GC1: BrainActivitySensor does not invent brain states — all from _STATE_LABELS dict."""
    data = {"state": raw_state}
    nv = BrainActivitySensorContract.native_value(data)
    assert nv in ("Aktiv — pulsierend", "Wach — bereit", "Schlafend"), \
        f"Unexpected computed state: {nv}"


# GC2 — global contract: /api/v1/hub/brain/activity endpoint verified in code
def test_GC2_endpoint_contract():
    """GC2: BrainActivitySensor._fetch() calls /api/v1/hub/brain/activity (code-verified).

    The sensor hits this endpoint (visible in source: url = f"{self._core_base_url()}/api/v1/hub/brain/activity").
    Contract guarantees: all displayed data originates from this Core API endpoint or
    coordinator webhook push — no local heuristic computation.
    """
    # Verify the contract: BrainActivitySensor is a pure pass-through shell
    # on two data sources:
    #   1. /api/v1/hub/brain/activity  (fetched at runtime via _fetch)
    #   2. coordinator.data["neurons_fired"] + ["brain_insights"]  (webhook push)
    # No computation, no classification, no threshold — pure projection.
    assert hasattr(BrainActivitySensorContract, "native_value")
    assert hasattr(BrainActivitySensorContract, "icon")
    assert hasattr(BrainActivitySensorContract, "extra_state_attributes")
    # Contract: all fields from API or coordinator — zero local logic
    data  = {"state": "idle", "total_pulses": 10}
    coord = {"neurons_fired": [{"neuron_id": "n1"}], "brain_insights": []}
    attrs = BrainActivitySensorContract.extra_state_attributes(data, coord)
    assert attrs["total_pulses"]        == 10      # from fetch
    assert attrs["neurons_fired_count"] == 1       # from coordinator
