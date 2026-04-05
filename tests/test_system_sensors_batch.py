"""Batch Projection Tests for hub_dashboard, system_integration, proactive_alert, weather_optimizer sensors.

All are Core-API sensors. Tests verify 200 parsing + 404 graceful degradation.
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


# ─── hub_dashboard_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_hub_dashboard_sensor_200():
    from custom_components.copilot_ha.sensors.hub_dashboard_sensor import HubDashboardSensor
    data = {"ok": True, "summary": "All systems operational", "active_modules": 4}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = HubDashboardSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs.get("active_modules") == 4


@pytest.mark.asyncio
async def test_hub_dashboard_sensor_404():
    from custom_components.copilot_ha.sensors.hub_dashboard_sensor import HubDashboardSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = HubDashboardSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── system_integration_sensor ────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_system_integration_sensor_200():
    from custom_components.copilot_ha.sensors.system_integration_sensor import SystemIntegrationSensor
    data = {"ok": True, "integrations": 12, "status": "healthy"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = SystemIntegrationSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 12


@pytest.mark.asyncio
async def test_system_integration_sensor_404():
    from custom_components.copilot_ha.sensors.system_integration_sensor import SystemIntegrationSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = SystemIntegrationSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── proactive_alert_sensor ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_proactive_alert_sensor_200():
    from custom_components.copilot_ha.sensors.proactive_alert_sensor import ProactiveAlertSensor
    data = {"ok": True, "alerts": 2, "critical": 0}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = ProactiveAlertSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 2


@pytest.mark.asyncio
async def test_proactive_alert_sensor_404():
    from custom_components.copilot_ha.sensors.proactive_alert_sensor import ProactiveAlertSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = ProactiveAlertSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── weather_optimizer_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_weather_optimizer_sensor_200():
    from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor
    data = {"ok": True, "savings_kwh": 2.4, "comfort_score": 0.88}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = WeatherOptimizerSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs.get("savings_kwh") == 2.4


@pytest.mark.asyncio
async def test_weather_optimizer_sensor_404():
    from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = WeatherOptimizerSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
