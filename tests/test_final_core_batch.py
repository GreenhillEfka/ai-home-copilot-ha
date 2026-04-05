"""Projection Contract Tests for automation_suggestion, ev_charging, fuel_price, weather_warning sensors.

All are Core-API sensors (hit /api/v1/regional or /api/v1/...). Tests verify:
- 200 response → correct state parsing
- 404/Error → graceful degradation (HA-83 pattern)
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


def make_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── automation_suggestion_sensor ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_automation_suggestion_sensor_200():
    from custom_components.copilot_ha.sensors.automation_suggestion_sensor import AutomationSuggestionSensor
    data = {"ok": True, "suggestions": ["Light dim at 22:00"], "count": 1, "confidence": 0.85}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = AutomationSuggestionSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["count"] == 1


@pytest.mark.asyncio
async def test_automation_suggestion_sensor_404():
    from custom_components.copilot_ha.sensors.automation_suggestion_sensor import AutomationSuggestionSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = AutomationSuggestionSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── ev_charging_sensor ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_ev_charging_sensor_200():
    from custom_components.copilot_ha.sensors.ev_charging_sensor import EVChargingSensor
    data = {"ok": True, "charging": True, "rate_kw": 11.0, "soc_percent": 65}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EVChargingSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["rate_kw"] == 11.0


@pytest.mark.asyncio
async def test_ev_charging_sensor_404():
    from custom_components.copilot_ha.sensors.ev_charging_sensor import EVChargingSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = EVChargingSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── fuel_price_sensor ──────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_fuel_price_sensor_200():
    from custom_components.copilot_ha.sensors.fuel_price_sensor import FuelPriceSensor
    data = {"ok": True, "fuel_type": "gas", "price_eur_l": 1.85, "currency": "EUR"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = FuelPriceSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 1.85


@pytest.mark.asyncio
async def test_fuel_price_sensor_404():
    from custom_components.copilot_ha.sensors.fuel_price_sensor import FuelPriceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = FuelPriceSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── weather_warning_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_weather_warning_sensor_200():
    from custom_components.copilot_ha.sensors.weather_warning_sensor import WeatherWarningSensor
    data = {"ok": True, "warnings": 2, "severity": "moderate", "types": ["rain", "wind"]}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = WeatherWarningSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 2


@pytest.mark.asyncio
async def test_weather_warning_sensor_404():
    from custom_components.copilot_ha.sensors.weather_warning_sensor import WeatherWarningSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = WeatherWarningSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
