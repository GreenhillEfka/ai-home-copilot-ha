"""Projection Contract Tests for calendar_sensors (HA-101).

Verifies: calendar_sensors.py is HA-lokal — reads HA coordinator only.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {
        "calendar_load": 0.55,
        "meetings_today": 3,
        "meetings_this_week": 12,
        "focus_time_available": 2.5,
    }
    return coordinator


@pytest.fixture
def mock_hass():
    return MagicMock()


@pytest.mark.asyncio
async def test_calendar_load_sensor_state(mock_coordinator, mock_hass):
    """CalendarLoadSensor reads coordinator data."""
    from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor
    sensor = CalendarLoadSensor(mock_coordinator, mock_hass)
    assert sensor.native_value == 0.55
    attrs = sensor.extra_state_attributes
    assert attrs["meetings_today"] == 3
    assert attrs["focus_time_available"] == 2.5


@pytest.mark.asyncio
async def test_calendar_load_sensor_ha_lokal(mock_coordinator, mock_hass):
    """CalendarLoadSensor is HA-lokal — coordinator-only, no Core API."""
    from custom_components.copilot_ha.sensors.calendar_sensors import CalendarLoadSensor
    sensor = CalendarLoadSensor(mock_coordinator, mock_hass)
    assert sensor._attr_should_poll is True
    assert not hasattr(sensor, '_core_base_url')
