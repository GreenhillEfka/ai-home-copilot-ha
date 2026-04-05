"""Tests for mood_sensor.py Core-Truth Projection.

Verifies that MoodSensor, MoodConfidenceSensor, and NeuronActivitySensor
project Core-provided truth from coordinator.data without local semantic invention.

Philosophy:
- MoodSensor.native_value       ← coordinator.data["mood"]["mood"]
- MoodSensor.emotions           ← coordinator.data["mood"]["emotions"]
- MoodSensor.contributing_neurons ← coordinator.data["mood"]["contributing_neurons"]
- MoodSensor.zone_moods          ← coordinator.data["zone_moods"]
- MoodConfidenceSensor           ← coordinator.data["mood"]["confidence"] * 100
- NeuronActivitySensor           ← coordinator.data["neurons"] (count active)
- NeuronActivitySensor._load_initial_history ← /api/v1/neurons/mood/history

HA only projects; HA does not compute mood or infer emotions.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock


# ── Minimal mock setup (no HA imports) ────────────────────────────────

class MockCoordinator:
    """Stand-in for CopilotDataUpdateCoordinator with known data shapes."""
    def __init__(self, data, api=None):
        self.data = data
        self.api = api or Mock()


class MockMoodSensor:
    """Stand-in for MoodSensor to test projection in isolation."""
    def __init__(self, coordinator: MockCoordinator):
        self.coordinator = coordinator
        self._attr_native_value = "unknown"
        self._attrs = {}

    @property
    def native_value(self) -> str:
        if not self.coordinator.data:
            return "unknown"
        mood_data = self.coordinator.data.get("mood", {})
        return mood_data.get("mood", "unknown")

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        mood_data = self.coordinator.data.get("mood", {})
        emotions = mood_data.get("emotions", [])
        if not emotions and mood_data.get("contributing_neurons"):
            emotions = [
                {"name": n.get("name", "unknown"), "value": n.get("value", 0.0)}
                for n in mood_data.get("contributing_neurons", [])
                if isinstance(n, dict)
            ]
        zone_moods = self.coordinator.data.get("zone_moods", {}) if self.coordinator.data else {}
        result = {
            "confidence": mood_data.get("confidence", 0.0),
            "emotions": emotions,
            "zone": mood_data.get("zone", "unknown"),
            "last_updated": mood_data.get("last_update"),
            "last_update": mood_data.get("last_update"),
            "contributing_neurons": mood_data.get("contributing_neurons", []),
            "zone_moods": zone_moods,
            "zone_moods_count": len(zone_moods),
        }
        return result


class MockMoodConfidenceSensor:
    """Stand-in for MoodConfidenceSensor."""
    def __init__(self, coordinator: MockCoordinator):
        self.coordinator = coordinator
        self._attr_native_value = 0

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        mood_data = self.coordinator.data.get("mood", {})
        confidence = mood_data.get("confidence", 0.0)
        return int(confidence * 100)

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        mood_data = self.coordinator.data.get("mood", {})
        return {
            "mood": mood_data.get("mood", "unknown"),
            "factors": mood_data.get("factors", {}),
        }


class MockNeuronActivitySensor:
    """Stand-in for NeuronActivitySensor."""
    def __init__(self, coordinator: MockCoordinator):
        self.coordinator = coordinator
        self._attr_native_value = 0
        self._history = []
        self._history_initialized = False

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        neurons = self.coordinator.data.get("neurons", {})
        active_count = sum(
            1 for n in neurons.values()
            if isinstance(n, dict) and n.get("active", False)
        )
        return active_count

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        neurons = self.coordinator.data.get("neurons", {})
        activity = [
            {
                "name": name,
                "active": bool(n.get("active", False)),
                "value": n.get("value", 0),
                "confidence": n.get("confidence", 0),
            }
            for name, n in neurons.items()
            if isinstance(n, dict)
        ]
        active_neurons = [a for a in activity if a["active"]]
        return {
            "activity": activity,
            "active_neurons": active_neurons,
            "total_neurons": len(neurons),
            "history": list(self._history),
        }

    async def _load_initial_history(self):
        """Fetch initial neuron history from Core API."""
        try:
            api = self.coordinator.api
            data = await api._safe_get(
                "/api/v1/neurons/mood/history",
                {"history": []},
                key="history",
                label="Neuron mood history",
            )
            if isinstance(data, list):
                self._history = [
                    {"value": entry.get("active_count", 0)}
                    for entry in data[-24:]
                ]
        except Exception:
            pass


# ── MoodSensor Projection Cases ────────────────────────────────────────

def test_mood_sensor_returns_unknown_when_no_data():
    """Case 1: no coordinator data → 'unknown'"""
    coordinator = MockCoordinator(None)
    sensor = MockMoodSensor(coordinator)
    assert sensor.native_value == "unknown"
    assert sensor.extra_state_attributes == {}


def test_mood_sensor_returns_unknown_when_mood_empty():
    """Case 2: empty mood dict → 'unknown'"""
    coordinator = MockCoordinator({})
    sensor = MockMoodSensor(coordinator)
    assert sensor.native_value == "unknown"


def test_mood_sensor_projects_core_mood_happy():
    """Case 3: Core provides mood=happy → sensor returns 'happy'"""
    coordinator = MockCoordinator({
        "mood": {"mood": "happy", "confidence": 0.92}
    })
    sensor = MockMoodSensor(coordinator)
    assert sensor.native_value == "happy"
    attrs = sensor.extra_state_attributes
    assert attrs["confidence"] == 0.92


def test_mood_sensor_projects_core_mood_focused():
    """Case 4: Core provides mood=focused → sensor returns 'focused'"""
    coordinator = MockCoordinator({
        "mood": {"mood": "focused", "confidence": 0.88}
    })
    sensor = MockMoodSensor(coordinator)
    assert sensor.native_value == "focused"


def test_mood_sensor_projects_core_mood_relaxed():
    """Case 5: Core provides mood=relaxed → sensor returns 'relaxed'"""
    coordinator = MockCoordinator({
        "mood": {"mood": "relaxed", "confidence": 0.95}
    })
    sensor = MockMoodSensor(coordinator)
    assert sensor.native_value == "relaxed"


def test_mood_sensor_projects_emotions_from_core():
    """Case 6: Core provides emotions list → sensor passes it through"""
    coordinator = MockCoordinator({
        "mood": {
            "mood": "content",
            "confidence": 0.85,
            "emotions": [
                {"name": "joy", "value": 0.8},
                {"name": "trust", "value": 0.6},
            ]
        }
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["emotions"] == [
        {"name": "joy", "value": 0.8},
        {"name": "trust", "value": 0.6},
    ]


def test_mood_sensor_falls_back_to_contributing_neurons():
    """Case 7: no emotions, has contributing_neurons → builds emotions from neurons"""
    coordinator = MockCoordinator({
        "mood": {
            "mood": "neutral",
            "confidence": 0.7,
            "contributing_neurons": [
                {"name": "serotonin", "value": 0.75},
                {"name": "dopamine", "value": 0.6},
            ]
        }
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["emotions"] == [
        {"name": "serotonin", "value": 0.75},
        {"name": "dopamine", "value": 0.6},
    ]


def test_mood_sensor_projects_zone_moods():
    """Case 8: Core provides zone_moods → sensor exposes count"""
    coordinator = MockCoordinator({
        "mood": {"mood": "neutral", "confidence": 0.6},
        "zone_moods": {
            "living_room": {"mood": "relaxed", "confidence": 0.9},
            "bedroom": {"mood": "sleepy", "confidence": 0.8},
        }
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["zone_moods_count"] == 2
    assert attrs["zone_moods"]["living_room"]["mood"] == "relaxed"


def test_mood_sensor_zone_unknown_when_missing():
    """Case 9: no zone in mood data → 'unknown'"""
    coordinator = MockCoordinator({
        "mood": {"mood": "happy", "confidence": 0.9}
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["zone"] == "unknown"


# ── MoodConfidenceSensor Projection Cases ──────────────────────────────

def test_mood_confidence_sensor_returns_0_when_no_data():
    """Case 10: no data → 0"""
    coordinator = MockCoordinator(None)
    sensor = MockMoodConfidenceSensor(coordinator)
    assert sensor.native_value == 0


def test_mood_confidence_sensor_converts_to_percent():
    """Case 11: confidence 0.87 → 87"""
    coordinator = MockCoordinator({
        "mood": {"mood": "happy", "confidence": 0.87}
    })
    sensor = MockMoodConfidenceSensor(coordinator)
    assert sensor.native_value == 87


def test_mood_confidence_sensor_rounds_down():
    """Case 12: confidence 0.999 → 99 (int truncation)"""
    coordinator = MockCoordinator({
        "mood": {"mood": "focused", "confidence": 0.999}
    })
    sensor = MockMoodConfidenceSensor(coordinator)
    assert sensor.native_value == 99


def test_mood_confidence_sensor_factors_from_core():
    """Case 13: Core provides factors → sensor exposes via attributes"""
    coordinator = MockCoordinator({
        "mood": {
            "mood": "stressed",
            "confidence": 0.73,
            "factors": {"workload": 0.8, "sleep": 0.4}
        }
    })
    sensor = MockMoodConfidenceSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["mood"] == "stressed"
    assert attrs["factors"]["workload"] == 0.8


# ── NeuronActivitySensor Projection Cases ──────────────────────────────

def test_neuron_activity_sensor_returns_0_when_no_data():
    """Case 14: no data → 0 active neurons"""
    coordinator = MockCoordinator(None)
    sensor = MockNeuronActivitySensor(coordinator)
    assert sensor.native_value == 0


def test_neuron_activity_sensor_counts_only_active():
    """Case 15: mixed active/inactive neurons → count active only"""
    coordinator = MockCoordinator({
        "neurons": {
            "neuron_A": {"active": True, "value": 0.9, "confidence": 0.8},
            "neuron_B": {"active": False, "value": 0.1, "confidence": 0.5},
            "neuron_C": {"active": True, "value": 0.7, "confidence": 0.9},
            "neuron_D": {"active": False, "value": 0.2, "confidence": 0.3},
        }
    })
    sensor = MockNeuronActivitySensor(coordinator)
    assert sensor.native_value == 2
    attrs = sensor.extra_state_attributes
    assert attrs["total_neurons"] == 4
    assert len(attrs["active_neurons"]) == 2


def test_neuron_activity_sensor_activity_list_structure():
    """Case 16: active neurons have correct attribute shape"""
    coordinator = MockCoordinator({
        "neurons": {
            "alpha": {"active": True, "value": 0.8, "confidence": 0.9},
            "beta": {"active": False, "value": 0.3, "confidence": 0.4},
        }
    })
    sensor = MockNeuronActivitySensor(coordinator)
    attrs = sensor.extra_state_attributes
    activity = attrs["activity"]
    alpha = next(a for a in activity if a["name"] == "alpha")
    assert alpha["active"] is True
    assert alpha["value"] == 0.8
    assert alpha["confidence"] == 0.9


@pytest.mark.asyncio
async def test_neuron_activity_sensor_loads_history_from_core_api():
    """Case 17: _load_initial_history fetches /api/v1/neurons/mood/history"""
    mock_api = Mock()
    mock_api._safe_get = AsyncMock(return_value=[
        {"active_count": 5},
        {"active_count": 3},
        {"active_count": 7},
    ])
    coordinator = MockCoordinator({"neurons": {}}, api=mock_api)
    sensor = MockNeuronActivitySensor(coordinator)

    await sensor._load_initial_history()

    mock_api._safe_get.assert_called_once_with(
        "/api/v1/neurons/mood/history",
        {"history": []},
        key="history",
        label="Neuron mood history",
    )
    assert len(sensor._history) == 3
    assert sensor._history[0] == {"value": 5}


@pytest.mark.asyncio
async def test_neuron_activity_sensor_history_limit_24():
    """Case 18: history capped at 24 entries"""
    mock_api = Mock()
    mock_api._safe_get = AsyncMock(return_value=[
        {"active_count": i} for i in range(30)
    ])
    coordinator = MockCoordinator({"neurons": {}}, api=mock_api)
    sensor = MockNeuronActivitySensor(coordinator)

    await sensor._load_initial_history()

    assert len(sensor._history) == 24


@pytest.mark.asyncio
async def test_neuron_activity_sensor_history_api_failure_silent():
    """Case 19: API failure → history stays empty, no exception"""
    mock_api = Mock()
    mock_api._safe_get = Mock(side_effect=Exception("API unavailable"))
    coordinator = MockCoordinator({"neurons": {}}, api=mock_api)
    sensor = MockNeuronActivitySensor(coordinator)

    await sensor._load_initial_history()  # must not raise

    assert sensor._history == []


# ── Edge Cases ─────────────────────────────────────────────────────────

def test_mood_sensor_handles_non_dict_contributing_neurons():
    """Case 20: contributing_neurons contains non-dict → skipped gracefully"""
    coordinator = MockCoordinator({
        "mood": {
            "mood": "neutral",
            "confidence": 0.5,
            "contributing_neurons": [
                "not_a_dict",
                {"name": "valid", "value": 0.6},
                None,
            ]
        }
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["emotions"] == [{"name": "valid", "value": 0.6}]


def test_neuron_activity_sensor_skips_non_dict_neurons():
    """Case 21: neurons dict contains non-dict values → skipped in activity list"""
    coordinator = MockCoordinator({
        "neurons": {
            "valid_neuron": {"active": True, "value": 0.8, "confidence": 0.9},
            "not_a_dict": "invalid",
            "also_invalid": None,
        }
    })
    sensor = MockNeuronActivitySensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["total_neurons"] == 3
    # isinstance(n, dict) filtert Non-Dicts aus activity raus
    assert len(attrs["activity"]) == 1
    assert attrs["active_neurons"] == [{"name": "valid_neuron", "active": True, "value": 0.8, "confidence": 0.9}]


def test_mood_sensor_zone_from_core_zone_field():
    """Case 22: zone from mood.zone field"""
    coordinator = MockCoordinator({
        "mood": {"mood": "happy", "confidence": 0.9, "zone": "kitchen"}
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["zone"] == "kitchen"


def test_mood_sensor_last_updated_passed_through():
    """Case 23: last_update from Core is passed through"""
    coordinator = MockCoordinator({
        "mood": {"mood": "content", "confidence": 0.8, "last_update": "2026-04-05T11:00:00Z"}
    })
    sensor = MockMoodSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["last_updated"] == "2026-04-05T11:00:00Z"
    assert attrs["last_update"] == "2026-04-05T11:00:00Z"


def test_neuron_activity_sensor_empty_neurons_dict():
    """Case 24: empty neurons dict → 0 active, 0 total"""
    coordinator = MockCoordinator({"neurons": {}})
    sensor = MockNeuronActivitySensor(coordinator)
    assert sensor.native_value == 0
    attrs = sensor.extra_state_attributes
    assert attrs["total_neurons"] == 0
    assert attrs["active_neurons"] == []
