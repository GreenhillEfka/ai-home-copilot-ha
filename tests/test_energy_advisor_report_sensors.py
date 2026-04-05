"""Projection Contract Tests for energy_advisor and energy_report sensors.

These are Core-API sensors. Tests verify 200 → correct parsing and 404 graceful degradation.
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


def make_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── energy_advisor_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_advisor_sensor_200():
    """Core returns 200 — parses advice."""
    from custom_components.copilot_ha.sensors.energy_advisor_sensor import EnergyAdvisorSensor
    data = {"ok": True, "advice": ["Shift laundry to off-peak"], "savings_potential_eur": 12.50}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyAdvisorSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "OK"
    attrs = sensor.extra_state_attributes
    assert attrs["advice"] == ["Shift laundry to off-peak"]


@pytest.mark.asyncio
async def test_energy_advisor_sensor_404():
    """404 → graceful degradation."""
    from custom_components.copilot_ha.sensors.energy_advisor_sensor import EnergyAdvisorSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = EnergyAdvisorSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    # Should not crash
    assert sensor.native_value in ["unavailable", "unknown", None]


# ─── energy_report_sensor ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_energy_report_sensor_200():
    """Core returns 200 — parses report."""
    from custom_components.copilot_ha.sensors.energy_report_sensor import EnergyReportSensor
    data = {"ok": True, "report_url": "http://core:8765/api/v1/energy/reports/1", "period": "weekly"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = EnergyReportSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["period"] == "weekly"


@pytest.mark.asyncio
async def test_energy_report_sensor_404():
    """404 → graceful degradation."""
    from custom_components.copilot_ha.sensors.energy_report_sensor import EnergyReportSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = EnergyReportSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value in [None, "unavailable"]
