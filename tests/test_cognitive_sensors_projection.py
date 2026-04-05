"""Projection Contract Tests for cognitive_sensors (HA-100).

Verifies: cognitive_sensors.py is HA-lokal — reads HA states only,
no Core API dependency. Contract: coordinator data → sensor state.
"""
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock()
    coordinator.data = {
        "attention_load": 0.73,
        "stress_proxy": 0.45,
        "cognitive_bottleneck": "memory",
        "session_count": 4,
    }
    return coordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    return hass


@pytest.mark.asyncio
async def test_attention_load_sensor_state(mock_coordinator, mock_hass):
    """AttentionLoadSensor reads coordinator data correctly."""
    from custom_components.copilot_ha.sensors.cognitive_sensors import AttentionLoadSensor
    sensor = AttentionLoadSensor(mock_coordinator, mock_hass)
    assert sensor.native_value == 0.73
    assert sensor.extra_state_attributes["stress_proxy"] == 0.45
    assert sensor.extra_state_attributes["bottleneck"] == "memory"


@pytest.mark.asyncio
async def test_attention_load_sensor_pollable(mock_coordinator, mock_hass):
    """AttentionLoadSensor has _attr_should_poll = True (HA-lokal polling)."""
    from custom_components.copilot_ha.sensors.cognitive_sensors import AttentionLoadSensor
    sensor = AttentionLoadSensor(mock_coordinator, mock_hass)
    assert sensor._attr_should_poll is True


@pytest.mark.asyncio
async def test_cognitive_state_no_core_dependency(mock_coordinator, mock_hass):
    """Cognitive sensors use only HA coordinator — no Core API calls."""
    from custom_components.copilot_ha.sensors.cognitive_sensors import AttentionLoadSensor
    sensor = AttentionLoadSensor(mock_coordinator, mock_hass)
    # Should not have _core_base_url or _core_headers
    assert not hasattr(sensor, '_core_base_url')
    assert not hasattr(sensor, '_core_headers')
