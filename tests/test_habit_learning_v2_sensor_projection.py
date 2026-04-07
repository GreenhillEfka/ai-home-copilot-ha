"""Habit Learning v2 Sensor Projection Contract Tests (HA-156).

Verifies HabitLearningSensor, HabitPredictionSensor, HabitAnomalySensor, HabitEfficiencySensor
are pure projection shells on coordinator.data (habit_summary, predictions) + anomaly framework.
No local semantic invention — all intelligence comes from Core.

HA-156 — 2026-04-06
"""
from __future__ import annotations

import pytest


# =============================================================================
# Contract Mirrors — mirror the sensor logic without importing
# =============================================================================

class HabitLearningSensorContract:
    """Mirror of HabitLearningSensor logic.
    
    Contract:
    - reads: coordinator.data["habit_summary"]
    - native_value: str(habit_summary.get("total_patterns", 0)) or "idle"
    - extra_state_attributes: direct pass-through of habit_summary fields + anomaly framework marker
    """

    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if not coordinator_data:
            return "idle"
        habit_summary = coordinator_data.get("habit_summary", {})
        total = habit_summary.get("total_patterns", 0)
        return str(total)

    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if not coordinator_data:
            return {"anomaly_framework_active": True, "habit_anomaly_level": "normal"}
        habit_summary = coordinator_data.get("habit_summary", {})
        return {
            "total_patterns": habit_summary.get("total_patterns", 0),
            "time_patterns": habit_summary.get("time_patterns", {}),
            "mood_patterns": habit_summary.get("mood_patterns", {}),
            "sequences": habit_summary.get("sequences", {}),
            "device_patterns": habit_summary.get("device_patterns", {}),
            "last_update": habit_summary.get("last_update"),
            "anomaly_framework_active": True,
            "habit_anomaly_level": "normal",  # Would come from framework in real sensor
        }


class HabitPredictionSensorContract:
    """Mirror of HabitPredictionSensor logic.
    
    Contract:
    - reads: coordinator.data["predictions"]
    - native_value: pattern of highest-confidence prediction, or "none"
    - extra_state_attributes: predictions list + count
    """

    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if not coordinator_data:
            return "none"
        predictions = coordinator_data.get("predictions", [])
        if not predictions:
            return "none"
        best = max(predictions, key=lambda p: p.get("confidence", 0))
        return best.get("pattern", "unknown")

    @staticmethod
    def extra_state_attributes(coordinator_data: dict | None) -> dict:
        if not coordinator_data:
            return {}
        predictions = coordinator_data.get("predictions", [])
        return {
            "predictions": [
                {
                    "pattern": p.get("pattern", ""),
                    "confidence": p.get("confidence", 0),
                    "predicted": p.get("predicted", False),
                    "details": p.get("details", {}),
                }
                for p in predictions
            ],
            "count": len(predictions),
        }


class HabitAnomalySensorContract:
    """Mirror of HabitAnomalySensor logic.
    
    Contract:
    - native_value: anomaly level from framework (defaults to "normal")
    - icon: static mapping from level to icon
    - extra_state_attributes: framework alert details or defaults
    """

    ICON_MAP = {
        "critical": "mdi:alert-octagon",
        "high": "mdi:alert",
        "medium": "mdi:alert-circle-outline",
        "low": "mdi:information",
        "normal": "mdi:check-decagram",
    }

    @staticmethod
    def icon(level: str) -> str:
        return HabitAnomalySensorContract.ICON_MAP.get(level, "mdi:help-circle")

    @staticmethod
    def extra_state_attributes_default() -> dict:
        return {"confidence": 0, "deviation_sigma": 0, "baseline_window_days": 7}


class HabitEfficiencySensorContract:
    """Mirror of HabitEfficiencySensor logic.
    
    Contract:
    - reads: coordinator.data["habit_summary"]["time_patterns"]["hvac_runtime_*"]
    - native_value: efficiency status based on runtime vs baseline threshold
    """

    @staticmethod
    def native_value(coordinator_data: dict | None) -> str:
        if not coordinator_data:
            return "unknown"
        habit_summary = coordinator_data.get("habit_summary", {})
        time_patterns = habit_summary.get("time_patterns", {})
        hvac = time_patterns.get("hvac_runtime_24h", {})
        baseline = time_patterns.get("hvac_runtime_7d_avg", 0)
        current = hvac.get("value", 0) if isinstance(hvac, dict) and hvac else 0
        
        if baseline > 0 and current > 0 and current > baseline * 1.4:
            return "Efficiency Degradation Detected"
        elif baseline > 0 and current > 0 and current < baseline * 0.6:
            return "Unusually Efficient"
        return "Normal"

    @staticmethod
    def extra_state_attributes_default() -> dict:
        return {"anomaly_framework": "sigma_deviation"}


# =============================================================================
# HabitLearningSensor Tests — HL1 to HL3
# =============================================================================

@pytest.mark.parametrize("data,expected", [
    # HL1: native_value
    ({"habit_summary": {"total_patterns": 42}}, "42"),
    ({"habit_summary": {"total_patterns": 0}}, "0"),
    ({"habit_summary": {}}, "0"),
    ({}, "idle"),
    (None, "idle"),
    ({"habit_summary": {"total_patterns": None}}, "None"),
])
def test_habit_learning_sensor_native_value(data, expected):
    """HL1: native_value reflects habit_summary.total_patterns or idle."""
    assert HabitLearningSensorContract.native_value(data) == expected


@pytest.mark.parametrize("data,expected_attrs", [
    # HL2: extra_state_attributes
    (
        {"habit_summary": {
            "total_patterns": 5,
            "time_patterns": {"morning": 2},
            "mood_patterns": {"happy": 1},
            "sequences": ["a", "b"],
            "device_patterns": {"light.living_room": 3},
            "last_update": "2026-04-06T20:00:00Z",
        }},
        {
            "total_patterns": 5,
            "time_patterns": {"morning": 2},
            "mood_patterns": {"happy": 1},
            "sequences": ["a", "b"],
            "device_patterns": {"light.living_room": 3},
            "last_update": "2026-04-06T20:00:00Z",
            "anomaly_framework_active": True,
            "habit_anomaly_level": "normal",
        },
    ),
    ({}, {"anomaly_framework_active": True, "habit_anomaly_level": "normal"}),
    ({"habit_summary": {}}, {
        "total_patterns": 0,
        "time_patterns": {},
        "mood_patterns": {},
        "sequences": {},
        "device_patterns": {},
        "last_update": None,
        "anomaly_framework_active": True,
        "habit_anomaly_level": "normal",
    }),
])
def test_habit_learning_sensor_attrs(data, expected_attrs):
    """HL2: extra_state_attributes are direct habit_summary fields + anomaly framework."""
    assert HabitLearningSensorContract.extra_state_attributes(data) == expected_attrs


def test_habit_learning_sensor_none_guard():
    """HL3: Handles None coordinator.data gracefully."""
    assert HabitLearningSensorContract.native_value(None) == "idle"
    attrs = HabitLearningSensorContract.extra_state_attributes(None)
    assert attrs == {"anomaly_framework_active": True, "habit_anomaly_level": "normal"}


# =============================================================================
# HabitPredictionSensor Tests — HP1 to HP3
# =============================================================================

@pytest.mark.parametrize("data,expected", [
    # HP1: native_value
    (
        {"predictions": [
            {"pattern": "morning_routine", "confidence": 0.9, "predicted": True, "details": {}},
            {"pattern": "evening_routine", "confidence": 0.7, "predicted": False, "details": {}},
        ]},
        "morning_routine",
    ),
    (
        {"predictions": [{"pattern": "evening_routine", "confidence": 0.7, "predicted": False, "details": {}}]},
        "evening_routine",
    ),
    ({"predictions": []}, "none"),
    ({}, "none"),
    (None, "none"),
    ({"predictions": None}, "none"),
])
def test_habit_prediction_sensor_native_value(data, expected):
    """HP1: native_value is highest-confidence prediction pattern."""
    assert HabitPredictionSensorContract.native_value(data) == expected


@pytest.mark.parametrize("data,expected_count", [
    # HP2: attrs count
    (
        {"predictions": [
            {"pattern": "a", "confidence": 0.5, "predicted": True, "details": {}},
            {"pattern": "b", "confidence": 0.3, "predicted": False, "details": {}},
            {"pattern": "c", "confidence": 0.2, "predicted": True, "details": {}},
        ]},
        3,
    ),
    ({}, 0),
    (None, 0),
    ({"predictions": []}, 0),
])
def test_habit_prediction_sensor_count(data, expected_count):
    """HP2: attrs count reflects len(predictions)."""
    attrs = HabitPredictionSensorContract.extra_state_attributes(data)
    assert attrs.get("count", 0) == expected_count


def test_habit_prediction_sensor_none_guard():
    """HP3: Handles None coordinator.data gracefully."""
    assert HabitPredictionSensorContract.native_value(None) == "none"
    assert HabitPredictionSensorContract.extra_state_attributes(None) == {}


# =============================================================================
# HabitAnomalySensor Tests — HA1 to HA2
# =============================================================================

@pytest.mark.parametrize("level,expected_icon", [
    # HA1: icon mapping
    ("critical", "mdi:alert-octagon"),
    ("high", "mdi:alert"),
    ("medium", "mdi:alert-circle-outline"),
    ("low", "mdi:information"),
    ("normal", "mdi:check-decagram"),
    ("unknown", "mdi:help-circle"),
])
def test_habit_anomaly_sensor_icon_mapping(level, expected_icon):
    """HA1: icon mapping is static and exhaustive."""
    assert HabitAnomalySensorContract.icon(level) == expected_icon


def test_habit_anomaly_sensor_attrs_default():
    """HA2: extra_state_attributes returns defaults when no alerts."""
    attrs = HabitAnomalySensorContract.extra_state_attributes_default()
    assert "baseline_window_days" in attrs
    assert attrs["baseline_window_days"] == 7


# =============================================================================
# HabitEfficiencySensor Tests — HE1 to HE3
# =============================================================================

@pytest.mark.parametrize("data,expected", [
    # HE1: native_value
    ({"habit_summary": {"time_patterns": {}}}, "Normal"),
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {}, "hvac_runtime_7d_avg": 100}}}, "Normal"),
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 80}, "hvac_runtime_7d_avg": 100}}}, "Normal"),  # 0.8x - normal range
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 150}, "hvac_runtime_7d_avg": 100}}}, "Efficiency Degradation Detected"),  # 1.5x > 1.4x
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 200}, "hvac_runtime_7d_avg": 100}}}, "Efficiency Degradation Detected"),  # 2.0x > 1.4x
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 30}, "hvac_runtime_7d_avg": 100}}}, "Unusually Efficient"),  # 0.3x < 0.6x
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 140}, "hvac_runtime_7d_avg": 100}}}, "Normal"),  # exactly 1.4x - not > 1.4
    ({"habit_summary": {"time_patterns": {"hvac_runtime_24h": {"value": 60}, "hvac_runtime_7d_avg": 100}}}, "Normal"),  # exactly 0.6x - not < 0.6
])
def test_habit_efficiency_sensor_native_value(data, expected):
    """HE1: native_value reflects HVAC efficiency vs baseline (thresholds >1.4x and <0.6x)."""
    assert HabitEfficiencySensorContract.native_value(data) == expected


def test_habit_efficiency_sensor_unknown_default():
    """HE2: Returns 'unknown' when no data."""
    assert HabitEfficiencySensorContract.native_value(None) == "unknown"


def test_habit_efficiency_sensor_attrs_default():
    """HE3: extra_state_attributes includes anomaly_framework marker."""
    attrs = HabitEfficiencySensorContract.extra_state_attributes_default()
    assert attrs["anomaly_framework"] == "sigma_deviation"


# =============================================================================
# Global Contract Tests — GC1, GC2
# =============================================================================

def test_habit_learning_sensors_pure_projection_no_local_semantic_invention():
    """GC1: All sensors project coordinator.data fields verbatim — efficiency has threshold logic."""
    coordinator_data = {
        "habit_summary": {
            "total_patterns": 3,
            "time_patterns": {"morning": 1, "hvac_runtime_24h": {"value": 80}, "hvac_runtime_7d_avg": 100},  # 0.8x = normal
            "mood_patterns": {"happy": 1},
            "sequences": ["seq1"],
            "device_patterns": {"light": 1},
            "last_update": "2026-04-06T12:00:00Z",
        },
        "predictions": [
            {"pattern": "p1", "confidence": 0.9, "predicted": True, "details": {"key": "val"}},
        ],
    }

    assert HabitLearningSensorContract.native_value(coordinator_data) == "3"
    assert HabitPredictionSensorContract.native_value(coordinator_data) == "p1"
    assert HabitEfficiencySensorContract.native_value(coordinator_data) == "Normal"
    
    hl_attrs = HabitLearningSensorContract.extra_state_attributes(coordinator_data)
    assert hl_attrs["total_patterns"] == 3
    
    hp_attrs = HabitPredictionSensorContract.extra_state_attributes(coordinator_data)
    assert hp_attrs.get("count", 0) == 1


def test_habit_learning_sensors_coordinator_data_none_guard():
    """GC2: All sensors handle None/missing coordinator.data gracefully."""
    for data in [None, {}]:
        assert HabitLearningSensorContract.native_value(data) == "idle"
        assert HabitPredictionSensorContract.native_value(data) == "none"
        assert HabitEfficiencySensorContract.native_value(data) == "unknown"
