"""Projection Contract Tests for demand_response_sensor (HA-83/HA-88).

Verifies: Sensor degrades gracefully when Core endpoint is missing.
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
    def __init__(self, resp):
        self._resp = resp
    def get(self, *args, **kwargs):
        return self._resp


@pytest.fixture
def mock_entity():
    from custom_components.copilot_ha.sensors.demand_response_sensor import DemandResponseSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    entity = DemandResponseSensor(coordinator)
    entity.hass = MagicMock()
    return entity


@pytest.mark.asyncio
async def test_demand_response_200(mock_entity):
    """Core returns 200 — sensor parses signal level."""
    data = {
        "ok": True, "current_signal": 2,
        "active_signals": 3, "managed_devices": 5,
        "curtailed_devices": 2, "total_reduction_watts": 1500,
        "response_active": True
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(200, data))
        await mock_entity.async_update()

    assert mock_entity.native_value == "Moderate"
    attrs = mock_entity.extra_state_attributes
    assert attrs["signal_level"] == 2
    assert attrs["response_active"] is True


@pytest.mark.asyncio
async def test_demand_response_404_degrades_gracefully(mock_entity):
    """Core returns 404 — sensor state=Normal, no exception."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(404))
        await mock_entity.async_update()

    assert mock_entity.native_value == "Normal"
    assert mock_entity.extra_state_attributes["signal_level"] == 0


@pytest.mark.asyncio
async def test_demand_response_critical_signal(mock_entity):
    """Signal level 3 = Critical."""
    data = {"ok": True, "current_signal": 3}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(200, data))
        await mock_entity.async_update()

    assert mock_entity.native_value == "Critical"
    assert mock_entity.icon == "mdi:alert-octagon"
