"""Batch Projection Tests for environment_sensors, zone_presence_trigger, energy_insights.

All are HA-lokal (coordinator-only, no Core API).
"""
import pytest
from unittest.mock import MagicMock


def make_coord(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


# ─── environment_sensors ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_environment_sensors_ha_lokal():
    """EnvironmentSensors — HA-lokal, reads coordinator data."""
    from custom_components.copilot_ha.sensors.environment_sensors import EnvironmentSensors
    coord = make_coord(
        indoor_temp=21.5, indoor_humidity=45,
        outdoor_temp=8.2, air_quality="good"
    )
    sensor = EnvironmentSensors(coord)
    assert hasattr(sensor, 'native_value') or hasattr(sensor, '_attr_native_value')


@pytest.mark.asyncio
async def test_environment_sensors_no_core_api():
    """EnvironmentSensors has no Core API dependency."""
    from custom_components.copilot_ha.sensors.environment_sensors import EnvironmentSensors
    coord = make_coord(indoor_temp=22.0)
    sensor = EnvironmentSensors(coord)
    assert not hasattr(sensor, '_core_base_url')
    assert not hasattr(sensor, '_core_headers')


# ─── zone_presence_trigger ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_zone_presence_trigger_ha_lokal():
    """ZonePresenceTrigger — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.zone_presence_trigger import ZonePresenceTriggerSensor
    coord = make_coord(
        active_zone="living_room", presence_detected=True
    )
    sensor = ZonePresenceTriggerSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_zone_presence_trigger_state():
    """ZonePresenceTrigger reads coordinator state correctly."""
    from custom_components.copilot_ha.sensors.zone_presence_trigger import ZonePresenceTriggerSensor
    coord = make_coord(active_zone="kitchen", presence_detected=True)
    sensor = ZonePresenceTriggerSensor(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["active_zone"] == "kitchen"


# ─── energy_insights ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_insights_ha_lokal():
    """EnergyInsights — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.energy_insights import EnergyInsightsSensor
    coord = make_coord(
        insights=["Shift washing to night"],
        potential_savings_kwh=4.2
    )
    sensor = EnergyInsightsSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_energy_insights_state():
    """EnergyInsights reads coordinator data."""
    from custom_components.copilot_ha.sensors.energy_insights import EnergyInsightsSensor
    coord = make_coord(insights=["Better insulation"], potential_savings_kwh=8.1)
    sensor = EnergyInsightsSensor(coord)
    attrs = sensor.extra_state_attributes
    assert "Better insulation" in attrs["insights"]
