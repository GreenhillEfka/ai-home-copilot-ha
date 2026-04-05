"""Projection Contract Tests for remaining sensors (batch E — Core-API sensors).

Covers: agent_status_sensor, ev_charging_sensor, fuel_price_sensor,
weather_warning_sensor, zone_mode_sensor.
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


def make_core_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── agent_status_sensor ────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.agent_status_sensor import AgentStatusSensor

def make_coord(**kw):
    c = MagicMock()
    c.data = kw
    return c


@pytest.mark.asyncio
async def test_agent_status_sensor_ha_lokal():
    sensor = AgentStatusSensor(make_coord(status="running", active_agents=4, uptime_hours=72.5))
    assert not hasattr(sensor, '_core_base_url')


# ─── ev_charging_sensor ──────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.ev_charging_sensor import EVChargingSensor


@pytest.mark.asyncio
async def test_ev_charging_sensor_200():
    data = {"ok": True, "charging": True, "rate_kw": 11.0, "soc_percent": 65}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EVChargingSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["rate_kw"] == 11.0


@pytest.mark.asyncio
async def test_ev_charging_sensor_404():
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = EVChargingSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── fuel_price_sensor ──────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.fuel_price_sensor import FuelPriceSensor


@pytest.mark.asyncio
async def test_fuel_price_sensor_200():
    data = {"ok": True, "fuel_type": "gas", "price_eur_l": 1.85, "currency": "EUR"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = FuelPriceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 1.85


@pytest.mark.asyncio
async def test_fuel_price_sensor_404():
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = FuelPriceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── weather_warning_sensor ─────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.weather_warning_sensor import WeatherWarningSensor


@pytest.mark.asyncio
async def test_weather_warning_sensor_200():
    data = {"ok": True, "warnings": 2, "severity": "moderate", "types": ["rain", "wind"]}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = WeatherWarningSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 2


@pytest.mark.asyncio
async def test_weather_warning_sensor_404():
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = WeatherWarningSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── zone_mode_sensor ────────────────────────────────────────────────────────────
from custom_components.copilot_ha.sensors.zone_mode_sensor import ZoneModeSensor


@pytest.mark.asyncio
async def test_zone_mode_sensor_200():
    data = {"ok": True, "mode": "home", "active_zones": 3}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = ZoneModeSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "home"


@pytest.mark.asyncio
async def test_zone_mode_sensor_404():
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = ZoneModeSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
