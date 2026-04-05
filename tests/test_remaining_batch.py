"""Batch Projection Tests for remaining untested sensors (final sprint batch).

Covers 8 sensors: agent_status, anomaly_detection, battery_optimizer,
brain_activity, predictive_maintenance, presence_sensors, regional_context, zone_mode.
"""
import pytest
from unittest.mock import MagicMock
import asyncio


def make_coord(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


# ─── agent_status_sensor ────────────────────────────────────────────────────────
class FakeResp:
    def __init__(self, status, json_data=None):
        self._status = status
        self._json = json_data or {}
    status = property(lambda s: s._status)
    async def json(self): return self._json
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


class FakeSession:
    def __init__(self, resp): self._resp = resp
    def get(self, *args, **kwargs): return self._resp


@pytest.mark.asyncio
async def test_agent_status_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.agent_status_sensor import AgentStatusSensor
    coord = make_coord(status="running", active_agents=4, uptime_hours=72.5)
    sensor = AgentStatusSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_agent_status_sensor_state():
    from custom_components.copilot_ha.sensors.agent_status_sensor import AgentStatusSensor
    coord = make_coord(status="running", active_agents=4, uptime_hours=72.5)
    sensor = AgentStatusSensor(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["active_agents"] == 4


# ─── anomaly_detection_sensor ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_anomaly_detection_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.anomaly_detection_sensor import AnomalyDetectionSensor
    coord = make_coord(anomalies_detected=0, threshold=0.85)
    sensor = AnomalyDetectionSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_anomaly_detection_sensor_state():
    from custom_components.copilot_ha.sensors.anomaly_detection_sensor import AnomalyDetectionSensor
    coord = make_coord(anomalies_detected=3, threshold=0.85)
    sensor = AnomalyDetectionSensor(coord)
    assert sensor.native_value == 3


# ─── battery_optimizer_sensor ───────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_battery_optimizer_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.battery_optimizer_sensor import BatteryOptimizerSensor
    coord = make_coord(battery_level=85, discharging=False, solar_mode=True)
    sensor = BatteryOptimizerSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_battery_optimizer_sensor_state():
    from custom_components.copilot_ha.sensors.battery_optimizer_sensor import BatteryOptimizerSensor
    coord = make_coord(battery_level=85, discharging=False, solar_mode=True)
    sensor = BatteryOptimizerSensor(coord)
    assert sensor.native_value == 85


# ─── brain_activity_sensor ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_brain_activity_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.brain_activity_sensor import BrainActivitySensor
    coord = make_coord(active_modules=5, processed_events=128)
    sensor = BrainActivitySensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_brain_activity_sensor_state():
    from custom_components.copilot_ha.sensors.brain_activity_sensor import BrainActivitySensor
    coord = make_coord(active_modules=5, processed_events=128)
    sensor = BrainActivitySensor(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["active_modules"] == 5


# ─── predictive_maintenance_sensor ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predictive_maintenance_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.predictive_maintenance_sensor import PredictiveMaintenanceSensor
    coord = make_coord(predictions=[], confidence=0.82)
    sensor = PredictiveMaintenanceSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_predictive_maintenance_sensor_state():
    from custom_components.copilot_ha.sensors.predictive_maintenance_sensor import PredictiveMaintenanceSensor
    coord = make_coord(predictions=["HVAC filter soon"], confidence=0.82)
    sensor = PredictiveMaintenanceSensor(coord)
    attrs = sensor.extra_state_attributes
    assert "HVAC filter" in str(attrs["predictions"])


# ─── presence_sensors ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_presence_sensors_ha_lokal():
    from custom_components.copilot_ha.sensors.presence_sensors import PresenceSensors
    coord = make_coord(primary_person="Andreas", confidence=0.95)
    sensor = PresenceSensors(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_presence_sensors_state():
    from custom_components.copilot_ha.sensors.presence_sensors import PresenceSensors
    coord = make_coord(primary_person="Andreas", confidence=0.95)
    sensor = PresenceSensors(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["primary_person"] == "Andreas"


# ─── regional_context_sensor ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_regional_context_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.regional_context_sensor import RegionalContextSensor
    coord = make_coord(country="DE", region="Bavaria", tariff_active=True)
    sensor = RegionalContextSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_regional_context_sensor_state():
    from custom_components.copilot_ha.sensors.regional_context_sensor import RegionalContextSensor
    coord = make_coord(country="DE", region="Bavaria", tariff_active=True)
    sensor = RegionalContextSensor(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["country"] == "DE"


# ─── zone_mode_sensor ────────────────────────────────────────────────────────────
class FakeRespZone:
    def __init__(self, status, json_data=None):
        self._status = status
        self._json = json_data or {}
    status = property(lambda s: s._status)
    async def json(self): return self._json
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass


class FakeSessionZone:
    def __init__(self, resp): self._resp = resp
    def get(self, *args, **kwargs): return self._resp


@pytest.mark.asyncio
async def test_zone_mode_sensor_core_api():
    from custom_components.copilot_ha.sensors.zone_mode_sensor import ZoneModeSensor
    coord = MagicMock()
    coord._core_base_url = lambda: "http://core:8765"
    coord._core_headers = lambda: {"Authorization": "Bearer test"}
    from unittest.mock import patch
    data = {"ok": True, "mode": "home", "active_zones": 3}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSessionZone(FakeRespZone(200, data))
        sensor = ZoneModeSensor(coord)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "home"


@pytest.mark.asyncio
async def test_zone_mode_sensor_404():
    from custom_components.copilot_ha.sensors.zone_mode_sensor import ZoneModeSensor
    coord = MagicMock()
    coord._core_base_url = lambda: "http://core:8765"
    coord._core_headers = lambda: {"Authorization": "Bearer test"}
    from unittest.mock import patch
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSessionZone(FakeRespZone(404))
        sensor = ZoneModeSensor(coord)
        sensor.hass = MagicMock()
        await sensor.async_update()
