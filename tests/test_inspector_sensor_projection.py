"""test_inspector_sensor_projection.py — InspectorSensor projection contract (25 Cases)

Contract: InspectorSensor is a pure Projection-Shell on coordinator.data[type].
No local semantic invention — trivially counts sub-items or returns scalar.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─── Contract Mirror ─────────────────────────────────────────────────────────────

class InspectorSensorContract:
    """Mirror of InspectorSensor projection logic for test isolation."""
    INSPECTOR_SENSOR_TYPES = ["zones", "tags", "character", "mood"]

    @staticmethod
    def state(coordinator_data, sensor_type):
        if not coordinator_data:
            return "unknown"
        data = coordinator_data
        if sensor_type == "zones":
            zones = data.get("zones", {})
            return len(zones.get("zones", []))
        elif sensor_type == "tags":
            tags = data.get("tags", {})
            return len(tags.get("tags", []))
        elif sensor_type == "character":
            return data.get("character", {}).get("preset", "not set")
        elif sensor_type == "mood":
            return data.get("mood", {}).get("current", "unknown")
        return "unknown"

    @staticmethod
    def attrs(coordinator_data, sensor_type):
        if not coordinator_data:
            return {}
        data = coordinator_data
        if sensor_type == "zones":
            return {"zones": data.get("zones", {})}
        elif sensor_type == "tags":
            return {"tags": data.get("tags", {})}
        elif sensor_type == "character":
            return {"character": data.get("character", {})}
        elif sensor_type == "mood":
            return {"mood": data.get("mood", {})}
        return {}


# ─── IS1 — zones state ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("coordinator_data,expected", [
    ({"zones": {"zones": [{"id": "z1"}, {"id": "z2"}, {"id": "z3"}]}}, 3),
    ({"zones": {"zones": [{"id": "z1"}]}}, 1),
    ({"zones": {"zones": []}}, 0),
])
def test_IS1_zones_state(coordinator_data, expected):
    assert InspectorSensorContract.state(coordinator_data, "zones") == expected


# ─── IS2 — tags state ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("coordinator_data,expected", [
    ({"tags": {"tags": [{"id": "t1"}, {"id": "t2"}]}}, 2),
    ({"tags": {"tags": []}}, 0),
])
def test_IS2_tags_state(coordinator_data, expected):
    assert InspectorSensorContract.state(coordinator_data, "tags") == expected


# ─── IS3 — character state ────────────────────────────────────────────────────────

@pytest.mark.parametrize("coordinator_data,expected", [
    ({"character": {"preset": "max", "tone": "friendly"}}, "max"),
    ({"character": {"tone": "friendly"}}, "not set"),
    ({}, "unknown"),
])
def test_IS3_character_state(coordinator_data, expected):
    assert InspectorSensorContract.state(coordinator_data, "character") == expected


# ─── IS4 — mood state ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("coordinator_data,expected", [
    ({"mood": {"current": "focused", "intensity": 0.8}}, "focused"),
    ({"mood": {}}, "unknown"),
    ({}, "unknown"),
])
def test_IS4_mood_state(coordinator_data, expected):
    assert InspectorSensorContract.state(coordinator_data, "mood") == expected


# ─── IS5 — attrs by type ─────────────────────────────────────────────────────────

def test_IS5_zones_attrs():
    d = {"zones": {"zones": [{"id": "z1"}]}}
    attrs = InspectorSensorContract.attrs(d, "zones")
    assert attrs == {"zones": {"zones": [{"id": "z1"}]}}


def test_IS5_tags_attrs():
    d = {"tags": {"tags": [{"id": "t1"}, {"id": "t2"}]}}
    attrs = InspectorSensorContract.attrs(d, "tags")
    assert attrs == {"tags": {"tags": [{"id": "t1"}, {"id": "t2"}]}}


def test_IS5_character_attrs():
    d = {"character": {"preset": "max", "tone": "friendly"}}
    attrs = InspectorSensorContract.attrs(d, "character")
    assert attrs == {"character": {"preset": "max", "tone": "friendly"}}


def test_IS5_mood_attrs():
    d = {"mood": {"current": "focused", "intensity": 0.8}}
    attrs = InspectorSensorContract.attrs(d, "mood")
    assert attrs == {"mood": {"current": "focused", "intensity": 0.8}}


# ─── IS6 — edge: missing optional / empty coordinator ──────────────────────────

@pytest.mark.parametrize("sensor_type", ["zones", "tags", "character", "mood"])
def test_IS6_missing_coordinator(sensor_type):
    assert InspectorSensorContract.state(None, sensor_type) == "unknown"
    assert InspectorSensorContract.attrs(None, sensor_type) == {}


@pytest.mark.parametrize("sensor_type", ["zones", "tags", "character", "mood"])
def test_IS6_empty_coordinator_data(sensor_type):
    assert InspectorSensorContract.state({}, sensor_type) == "unknown"
    assert InspectorSensorContract.attrs({}, sensor_type) == {}


# ─── GC1 — global contract: pure projection, no local semantic invention ─────────

def test_GC1_pure_projection_no_local_semantics():
    """No threshold, no classification, no heuristic — just coordinator.data access."""
    for stype in InspectorSensorContract.INSPECTOR_SENSOR_TYPES:
        state = InspectorSensorContract.state({"any": "data"}, stype)
        # must not raise, must return deterministic scalar
        assert isinstance(state, (str, int, type(None)))


def test_GC2_all_sensor_types_covered():
    """All 4 inspector sensor types are accounted for."""
    assert InspectorSensorContract.INSPECTOR_SENSOR_TYPES == [
        "zones", "tags", "character", "mood"
    ]


# ─── GC3 — source guard: pilotsuite_* unique IDs, no stale ai_copilot_* strings ──

def _read_file(path):
    with open(path) as f:
        return f.read()

def test_GC3_inspector_uses_pilotsuite_unique_id_template():
    """InspectorSensor uses the pilotsuite_inspector_ unique ID template."""
    src = _read_file("custom_components/pilotsuite/sensors/inspector_sensor.py")
    assert 'f"pilotsuite_inspector_{sensor_type}"' in src

def test_GC3_no_stale_ai_copilot_inspector_template():
    """No stale ai_copilot_inspector_ unique ID template remains."""
    src = _read_file("custom_components/pilotsuite/sensors/inspector_sensor.py")
    assert 'f"ai_copilot_inspector_{sensor_type}"' not in src

def test_GC3_migration_map_entries_present():
    """Migration map in __init__.py covers all 4 legacy inspector unique IDs."""
    src = _read_file("custom_components/pilotsuite/__init__.py")
    for legacy, canonical in [
        ("ai_copilot_inspector_zones", "pilotsuite_inspector_zones"),
        ("ai_copilot_inspector_tags", "pilotsuite_inspector_tags"),
        ("ai_copilot_inspector_character", "pilotsuite_inspector_character"),
        ("ai_copilot_inspector_mood", "pilotsuite_inspector_mood"),
    ]:
        assert f'"{legacy}": "{canonical}"' in src, f"Missing migration: {legacy} -> {canonical}"
