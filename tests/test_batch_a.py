"""Projection Contract Tests for remaining untested sensors (batch A).

Covers: module_integration, media_follow, inspector, voice_context,
media_sensors, time_sensors, gas_meter_sensor.
"""
import pytest
from unittest.mock import MagicMock, patch


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


def make_coord(**kw):
    c = MagicMock()
    c.data = kw
    return c


def make_core_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── module_integration ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_module_integration_ha_lokal():
    from custom_components.copilot_ha.sensors.module_integration import ModuleIntegrationSensor
    sensor = ModuleIntegrationSensor(make_coord(active_modules=5, loaded=5))
    assert not hasattr(sensor, '_core_base_url')


# ─── media_follow_sensor ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_media_follow_sensor_200():
    from custom_components.copilot_ha.sensors.media_follow_sensor import MediaFollowSensor
    data = {"ok": True, "following": True, "media_title": "Jazz", "speaker": "Living Room"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = MediaFollowSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "following"


@pytest.mark.asyncio
async def test_media_follow_sensor_404():
    from custom_components.copilot_ha.sensors.media_follow_sensor import MediaFollowSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = MediaFollowSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── inspector_sensor ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_inspector_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    sensor = InspectorSensor(make_coord(zones=5, tags=12), "zones", "Habitus Zones", "mdi:floor-plan")
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == 5


# ─── voice_context ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_voice_context_ha_lokal():
    from custom_components.copilot_ha.sensors.voice_context import VoiceContextSensor
    sensor = VoiceContextSensor(make_coord(active_turns=3))
    assert not hasattr(sensor, '_core_base_url')


# ─── media_sensors ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_media_sensors_ha_lokal():
    from custom_components.copilot_ha.sensors.media_sensors import MediaSensors
    sensor = MediaSensors(make_coord(active_media="Jazz", volume=35))
    assert not hasattr(sensor, '_core_base_url')


# ─── time_sensors ──────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_time_sensors_ha_lokal():
    from custom_components.copilot_ha.sensors.time_sensors import TimeSensors
    sensor = TimeSensors(make_coord(current_time="18:45", day_of_week="Sunday"))
    assert not hasattr(sensor, '_core_base_url')


# ─── gas_meter_sensor ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_gas_meter_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.gas_meter_sensor import GasMeterSensor
    sensor = GasMeterSensor(make_coord(gas_consumption_m3=124.5, cost_eur=87.20))
    assert not hasattr(sensor, '_core_base_url')
