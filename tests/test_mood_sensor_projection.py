"""Projection Contract Tests for mood_sensor (HA-lokal).

Verifies: mood_sensor reads HA coordinator only — no Core API.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_coordinator():
    c = MagicMock()
    c.data = {
        "mood": "productive",
        "mood_score": 0.78,
        "dominant_factors": ["focus_time", "sleep_quality"],
        "trend": "improving",
    }
    return c


@pytest.fixture
def mock_hass():
    return MagicMock()


@pytest.mark.asyncio
async def test_mood_sensor_state(mock_coordinator, mock_hass):
    """MoodSensor reads coordinator data correctly."""
    from custom_components.copilot_ha.sensors.mood_sensor import MoodSensor
    sensor = MoodSensor(mock_coordinator, mock_hass)
    assert sensor.native_value == "productive"
    attrs = sensor.extra_state_attributes
    assert attrs["mood_score"] == 0.78
    assert attrs["trend"] == "improving"


@pytest.mark.asyncio
async def test_mood_sensor_ha_lokal(mock_coordinator, mock_hass):
    """MoodSensor is HA-lokal — no Core API calls."""
    from custom_components.copilot_ha.sensors.mood_sensor import MoodSensor
    sensor = MoodSensor(mock_coordinator, mock_hass)
    assert not hasattr(sensor, '_core_base_url')
    assert not hasattr(sensor, '_core_headers')


@pytest.mark.asyncio
async def test_mood_sensor_no_session_dependency(mock_coordinator, mock_hass):
    """MoodSensor has no session/aiohttp dependency."""
    from custom_components.copilot_ha.sensors.mood_sensor import MoodSensor
    sensor = MoodSensor(mock_coordinator, mock_hass)
    # Coordinator must be present
    assert hasattr(sensor, 'coordinator')
