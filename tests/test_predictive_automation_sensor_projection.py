"""Projection Contract Tests: predictive_automation_sensor.py

Verifies: PredictiveAutomationSensor is a pure projection shell on
coordinator.data["suggestions"] — no local semantic invention.

Contract verified:
- state = len(suggestions) as string ("idle"/"0"/"1"/"N")
- attrs = raw suggestion list + count + last_update
- No local ML/heuristics — all data from Core coordinator
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# === Fixtures ===

@pytest.fixture
def coordinator():
    return MagicMock()


@pytest.fixture
def sensor(coordinator):
    from custom_components.copilot_ha.sensors.predictive_automation import (
        PredictiveAutomationSensor,
    )
    return PredictiveAutomationSensor(coordinator)


# === PA1: native_value ===

def test_predictive_automation_sensor_pa1_no_data(coordinator, sensor):
    """PA1: No coordinator data → 'idle'"""
    coordinator.data = None
    sensor._handle_coordinator_update()
    assert sensor.native_value == "idle"


def test_predictive_automation_sensor_pa1_empty_list(coordinator, sensor):
    """PA1: Empty suggestions list → '0'"""
    coordinator.data = {"suggestions": [], "last_update": "2026-04-05T12:00:00Z"}
    sensor._handle_coordinator_update()
    assert sensor.native_value == "0"


def test_predictive_automation_sensor_pa1_one_suggestion(coordinator, sensor):
    """PA1: Single suggestion → '1'"""
    coordinator.data = {
        "suggestions": [{"id": "s1", "text": "Licht einschalten"}],
        "last_update": "2026-04-05T12:00:00Z",
    }
    sensor._handle_coordinator_update()
    assert sensor.native_value == "1"


def test_predictive_automation_sensor_pa1_multiple(coordinator, sensor):
    """PA1: Multiple suggestions → string count"""
    coordinator.data = {
        "suggestions": [
            {"id": "s1", "text": "Licht einschalten"},
            {"id": "s2", "text": "Heizung senken"},
            {"id": "s3", "text": "Musik abspielen"},
        ],
        "last_update": "2026-04-05T12:00:00Z",
    }
    sensor._handle_coordinator_update()
    assert sensor.native_value == "3"


def test_predictive_automation_sensor_pa1_missing_suggestions_key(coordinator, sensor):
    """PA1: suggestions key absent → treated as empty → '0'"""
    coordinator.data = {"last_update": "2026-04-05T12:00:00Z"}
    sensor._handle_coordinator_update()
    assert sensor.native_value == "0"


# === PA2: icon ===

def test_predictive_automation_sensor_pa2_icon(coordinator, sensor):
    """PA2: Icon is static mdi:auto-mode"""
    assert sensor.icon == "mdi:auto-mode"


# === PA3: extra_state_attributes ===

def test_predictive_automation_sensor_pa3_no_data(coordinator, sensor):
    """PA3: No data → zero counts, empty list"""
    coordinator.data = None
    sensor._handle_coordinator_update()
    attrs = sensor.extra_state_attributes
    assert attrs["suggestion_count"] == 0
    assert attrs["suggestions"] == []
    assert attrs["last_update"] is None


def test_predictive_automation_sensor_pa3_with_suggestions(coordinator, sensor):
    """PA3: Attributes carry raw suggestion list"""
    suggestions = [
        {"id": "s1", "text": "Licht einschalten"},
        {"id": "s2", "text": "Heizung senken"},
    ]
    coordinator.data = {"suggestions": suggestions, "last_update": "2026-04-05T12:00:00Z"}
    sensor._handle_coordinator_update()
    attrs = sensor.extra_state_attributes
    assert attrs["suggestion_count"] == 2
    assert attrs["suggestions"] == suggestions
    assert attrs["last_update"] == "2026-04-05T12:00:00Z"


def test_predictive_automation_sensor_pa3_empty_list(coordinator, sensor):
    """PA3: Empty list → count 0, empty suggestions list"""
    coordinator.data = {"suggestions": [], "last_update": "2026-04-05T12:00:00Z"}
    sensor._handle_coordinator_update()
    attrs = sensor.extra_state_attributes
    assert attrs["suggestion_count"] == 0
    assert attrs["suggestions"] == []


# === GC: Global Contract ===

def test_predictive_automation_sensor_gc1_pure_projection(coordinator, sensor):
    """GC1: Sensor reads only from coordinator.data['suggestions'] — pure projection shell"""
    suggestions = [{"id": "s1", "text": "Test"}]
    coordinator.data = {"suggestions": suggestions, "last_update": "2026-04-05T12:00:00Z"}
    sensor._handle_coordinator_update()

    # native_value derives from suggestions count — projection, not invention
    assert sensor.native_value == "1"

    # attrs carry raw suggestions — Core data, not HA-local transformation
    assert sensor.extra_state_attributes["suggestions"] == suggestions

    # No _action_to_voice, no local mood classification, no local priority sorting
    # Sensor is a thin shell over coordinator.data["suggestions"]


def test_predictive_automation_sensor_gc2_no_local_semantic_invention(coordinator, sensor):
    """GC2: No local semantic invention — all suggestion logic lives in Core"""
    coordinator.data = {
        "suggestions": [
            {"id": "s1", "text": "Licht einschalten", "confidence": 0.95},
            {"id": "s2", "text": "Heizung senken", "confidence": 0.80},
        ],
        "last_update": "2026-04-05T12:00:00Z",
    }
    sensor._handle_coordinator_update()

    # Sensor does NOT compute confidence scores locally
    # Sensor does NOT rank/filter suggestions locally
    # Sensor does NOT invent new suggestion types
    # It just passes through what Core provides
    attrs = sensor.extra_state_attributes
    assert attrs["suggestions"][0]["confidence"] == 0.95
    assert attrs["suggestions"][1]["confidence"] == 0.80
