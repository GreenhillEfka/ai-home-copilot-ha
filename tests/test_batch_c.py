"""Projection Contract Tests for remaining sensors (batch C).

Covers: energy_cost, energy_forecast, energy_sankey, energy_schedule,
energy_advisor, energy_report, weather_optimizer, predictive_automation,
predictive_maintenance, cross_dependency.
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


# ─── energy_cost_sensor ─────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_cost_sensor_200():
    from custom_components.copilot_ha.sensors.energy_cost_sensor import EnergyCostSensor
    data = {"ok": True, "total_cost_eur": 42.50, "period": "weekly"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyCostSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 42.50


@pytest.mark.asyncio
async def test_energy_cost_sensor_404():
    from custom_components.copilot_ha.sensors.energy_cost_sensor import EnergyCostSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = EnergyCostSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value is None


# ─── energy_forecast_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_forecast_sensor_200():
    from custom_components.copilot_ha.sensors.energy_forecast_sensor import EnergyForecastSensor
    data = {"ok": True, "forecast_kwh": 14.2, "confidence": 0.87}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyForecastSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 14.2


@pytest.mark.asyncio
async def test_energy_forecast_sensor_404():
    from custom_components.copilot_ha.sensors.energy_forecast_sensor import EnergyForecastSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = EnergyForecastSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── energy_sankey_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_sankey_sensor_200():
    from custom_components.copilot_ha.sensors.energy_sankey_sensor import EnergySankeySensor
    data = {"ok": True, "total_kwh": 28.4, "nodes": [], "links": []}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergySankeySensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 28.4


# ─── energy_schedule_sensor ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_schedule_sensor_200():
    from custom_components.copilot_ha.sensors.energy_schedule_sensor import EnergyScheduleSensor
    data = {"ok": True, "schedule_count": 5, "next_event": "2026-04-05T20:00"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyScheduleSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 5


# ─── energy_advisor_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_advisor_sensor_200():
    from custom_components.copilot_ha.sensors.energy_advisor_sensor import EnergyAdvisorSensor
    data = {"ok": True, "advice": ["Shift laundry"], "savings_potential_eur": 12.50}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyAdvisorSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["advice"] == ["Shift laundry"]


# ─── energy_report_sensor ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_report_sensor_200():
    from custom_components.copilot_ha.sensors.energy_report_sensor import EnergyReportSensor
    data = {"ok": True, "report_url": "http://core:8765/api/v1/energy/reports/1", "period": "weekly"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyReportSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["period"] == "weekly"


# ─── weather_optimizer_sensor ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_weather_optimizer_sensor_200():
    from custom_components.copilot_ha.sensors.weather_optimizer_sensor import WeatherOptimizerSensor
    data = {"ok": True, "savings_kwh": 2.4, "comfort_score": 0.88}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = WeatherOptimizerSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs.get("savings_kwh") == 2.4


# ─── predictive_automation_sensor ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predictive_automation_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.predictive_automation import PredictiveAutomationSensor
    c = MagicMock()
    c.data = {"automations": [], "next_trigger": None}
    sensor = PredictiveAutomationSensor(c)
    assert not hasattr(sensor, '_core_base_url')


# ─── predictive_maintenance_sensor ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predictive_maintenance_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.predictive_maintenance_sensor import PredictiveMaintenanceSensor
    c = MagicMock()
    c.data = {"predictions": [], "confidence": 0.82}
    sensor = PredictiveMaintenanceSensor(c)
    assert not hasattr(sensor, '_core_base_url')


# ─── cross_dependency_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cross_dependency_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.cross_dependency_sensor import CrossDependencySensor
    c = MagicMock()
    c.data = {"dependencies": [], "conflict_count": 0}
    sensor = CrossDependencySensor(c)
    assert not hasattr(sensor, '_core_base_url')
