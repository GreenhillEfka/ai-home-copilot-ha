"""Projection Contract Tests for energy cost/forecast/report/sankey/schedule sensors.

These sensors project Core API data into HA. Tests verify:
1. 200 response → correct state parsing
2. 404/Error → graceful degradation (HA-83 pattern)
3. HA-lokal fallback where no Core endpoint exists
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
    def __init__(self, resp=None): self._resp = resp
    def get(self, *args, **kwargs): return self._resp


# ─── energy_cost_sensor ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_cost_sensor_200():
    """Core returns 200 — parses weekly cost correctly."""
    from custom_components.copilot_ha.sensors.energy_cost_sensor import EnergyCostSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {
        "ok": True, "total_cost_eur": 42.50,
        "period": "weekly", "avg_daily_cost_eur": 6.07,
        "total_consumption_kwh": 185.3, "total_savings_eur": 8.20,
        "days_count": 7
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyCostSensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 42.50
    attrs = sensor.extra_state_attributes
    assert attrs["total_consumption_kwh"] == 185.3


@pytest.mark.asyncio
async def test_energy_cost_sensor_404_degrades():
    """404 → state=None, no crash."""
    from custom_components.copilot_ha.sensors.energy_cost_sensor import EnergyCostSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = EnergyCostSensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value is None


# ─── energy_forecast_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_forecast_sensor_200():
    """Core returns 200 — parses forecast correctly."""
    from custom_components.copilot_ha.sensors.energy_forecast_sensor import EnergyForecastSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {
        "ok": True, "forecast_kwh": 14.2, "confidence": 0.87,
        "peak_watts": 3200, "off_peak_kwh": 9.1
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyForecastSensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 14.2
    attrs = sensor.extra_state_attributes
    assert attrs["confidence"] == 0.87


@pytest.mark.asyncio
async def test_energy_forecast_sensor_404_degrades():
    """404 → state=None gracefully."""
    from custom_components.copilot_ha.sensors.energy_forecast_sensor import EnergyForecastSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = EnergyForecastSensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value is None


# ─── energy_sankey_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_sankey_sensor_200():
    """Core returns 200 — parses sankey data."""
    from custom_components.copilot_ha.sensors.energy_sankey_sensor import EnergySankeySensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {"ok": True, "total_kwh": 28.4, "nodes": [], "links": []}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergySankeySensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 28.4


# ─── energy_schedule_sensor ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_schedule_sensor_200():
    """Core returns 200 — parses schedule correctly."""
    from custom_components.copilot_ha.sensors.energy_schedule_sensor import EnergyScheduleSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {"ok": True, "schedule_count": 5, "next_event": "2026-04-05T20:00"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyScheduleSensor(coordinator)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 5
