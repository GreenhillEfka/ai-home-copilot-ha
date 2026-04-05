"""Projection Contract Tests for energy_sensors (HA-103).

Verifies: energy_sensors.py is HA-lokal — reads HA states + coordinator.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {
        "current_power_w": 850.0,
        "daily_energy_kwh": 12.4,
        "frugality_score": 0.71,
        "usage_level": "moderate",
    }
    return coordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.states = MagicMock()
    return hass


@pytest.mark.asyncio
async def test_energy_proxy_sensor_state(mock_coordinator, mock_hass):
    """EnergyProxySensor reads coordinator data correctly."""
    from custom_components.copilot_ha.sensors.energy_sensors import EnergyProxySensor
    sensor = EnergyProxySensor(mock_coordinator, mock_hass)
    assert sensor.native_value == 850.0
    attrs = sensor.extra_state_attributes
    assert attrs["daily_energy_kwh"] == 12.4
    assert attrs["frugality_score"] == 0.71


@pytest.mark.asyncio
async def test_energy_proxy_sensor_ha_lokal(mock_coordinator, mock_hass):
    """EnergyProxySensor is HA-lokal — no Core API calls."""
    from custom_components.copilot_ha.sensors.energy_sensors import EnergyProxySensor
    sensor = EnergyProxySensor(mock_coordinator, mock_hass)
    assert not hasattr(sensor, '_core_base_url')
    assert not hasattr(sensor, '_core_headers')


@pytest.mark.asyncio
async def test_energy_usage_level_enum(mock_coordinator, mock_hass):
    """Usage level enum maps correctly."""
    from custom_components.copilot_ha.sensors.energy_sensors import EnergyUsageLevel
    assert EnergyUsageLevel.MODERATE.value == "moderate"
    assert EnergyUsageLevel.HIGH.value == "high"
