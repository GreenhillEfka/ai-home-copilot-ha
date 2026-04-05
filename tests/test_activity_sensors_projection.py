"""Projection Contract Tests for activity_sensors (HA-102).

Verifies: activity_sensors.py reads HA coordinator — HA-lokal.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {
        "dominant_activity": "evening_relaxation",
        "activity_confidence": 0.82,
        "scene_active": "Evening Relaxation",
        "transition_detected": False,
    }
    return coordinator


@pytest.fixture
def mock_hass():
    return MagicMock()


@pytest.mark.asyncio
async def test_activity_sensors_state(mock_coordinator, mock_hass):
    """ActivitySensor reads coordinator data correctly."""
    from custom_components.copilot_ha.sensors.activity_sensors import ActivitySensor
    sensor = ActivitySensor(mock_coordinator, mock_hass)
    assert sensor.native_value == "evening_relaxation"
    attrs = sensor.extra_state_attributes
    assert attrs["confidence"] == 0.82
    assert attrs["scene"] == "Evening Relaxation"


@pytest.mark.asyncio
async def test_activity_sensors_ha_lokal(mock_coordinator, mock_hass):
    """ActivitySensor is HA-lokal — coordinator-only, no Core API."""
    from custom_components.copilot_ha.sensors.activity_sensors import ActivitySensor
    sensor = ActivitySensor(mock_coordinator, mock_hass)
    assert not hasattr(sensor, '_core_base_url')
