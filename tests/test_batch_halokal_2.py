"""Projection Contract Tests for anomaly_alert, area_presence_sensor, brain_architecture_sensor.

All are HA-lokal (no Core API calls).
"""
import pytest
from unittest.mock import MagicMock


def make_coord(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


# ─── anomaly_alert ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_anomaly_alert_ha_lokal():
    """AnomalyAlertSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.anomaly_alert import AnomalyAlertSensor
    coord = make_coord(anomaly_detected=False, alert_level="normal")
    sensor = AnomalyAlertSensor(coord)
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == "normal"


# ─── area_presence_sensor ────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_area_presence_sensor_ha_lokal():
    """AreaPresenceSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.area_presence_sensor import AreaPresenceSensor
    coord = make_coord(area_id="living_room", presence_count=2)
    sensor = AreaPresenceSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── autonomy_status_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_autonomy_status_sensor_ha_lokal():
    """AutonomyStatusSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.autonomy_status_sensor import AutonomyStatusSensor
    coord = make_coord(autonomy_level=0.85, active_modes=["learning"])
    sensor = AutonomyStatusSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── brain_architecture_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_brain_architecture_sensor_ha_lokal():
    """BrainArchitectureSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.brain_architecture_sensor import BrainArchitectureSensor
    coord = make_coord(module_count=12, active_neurons=48)
    sensor = BrainArchitectureSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── gas_meter_sensor ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gas_meter_sensor_ha_lokal():
    """GasMeterSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.gas_meter_sensor import GasMeterSensor
    coord = make_coord(gas_consumption_m3=124.5, cost_eur=87.20)
    sensor = GasMeterSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── habit_learning_v2 ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_habit_learning_v2_ha_lokal():
    """HabitLearningV2Sensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.habit_learning_v2 import HabitLearningV2Sensor
    coord = make_coord(learned_habits=5, confidence=0.78)
    sensor = HabitLearningV2Sensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── light_intelligence_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_light_intelligence_sensor_ha_lokal():
    """LightIntelligenceSensor — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.light_intelligence_sensor import LightIntelligenceSensor
    coord = make_coord(brightness_avg=215, active_zones=3)
    sensor = LightIntelligenceSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── media_sensors ──────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_media_sensors_ha_lokal():
    """MediaSensors — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.media_sensors import MediaSensors
    coord = make_coord(active_media="Jazz", volume=35)
    sensor = MediaSensors(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── time_sensors ───────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_time_sensors_ha_lokal():
    """TimeSensors — HA-lokal, no Core API."""
    from custom_components.copilot_ha.sensors.time_sensors import TimeSensors
    coord = make_coord(current_time="18:45", day_of_week="Sunday")
    sensor = TimeSensors(coord)
    assert not hasattr(sensor, '_core_base_url')
