"""Projection Contract Tests for appliance_fingerprint_sensor (HA-83/HA-88).

Verifies: Sensor degrades gracefully when Core endpoints are missing.
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
    def __init__(self, resp=None):
        self._resp = resp
    def get(self, *args, **kwargs):
        return self._resp


@pytest.fixture
def mock_entity():
    from custom_components.copilot_ha.sensors.appliance_fingerprint_sensor import ApplianceFingerprintSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    entity = ApplianceFingerprintSensor(coordinator)
    entity.hass = MagicMock()
    return entity


@pytest.mark.asyncio
async def test_appliance_fingerprint_200(mock_entity):
    """Core returns 200 — sensor parses fingerprints correctly."""
    data = {
        "ok": True,
        "count": 3,
        "fingerprints": [
            {"device_id": "d1", "device_name": "Waschmaschine",
             "device_type": "washer", "avg_power_watts": 500}
        ]
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(200, data))
        await mock_entity.async_update()

    assert mock_entity.native_value == 3
    attrs = mock_entity.extra_state_attributes
    assert attrs["total_devices"] == 3
    assert len(attrs["fingerprints"]) == 1


@pytest.mark.asyncio
async def test_appliance_fingerprint_404_degrades_gracefully(mock_entity):
    """Core returns 404 — sensor state=0, no exception."""
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(404))
        await mock_entity.async_update()

    assert mock_entity.native_value == 0
    assert mock_entity.extra_state_attributes["total_devices"] == 0


@pytest.mark.asyncio
async def test_appliance_fingerprint_usage_404(mock_entity):
    """usage endpoint 404 — sensor continues without crashing."""
    data = {"ok": True, "count": 2, "fingerprints": []}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_session_fn:
        mock_session_fn.return_value = FakeSession(FakeResp(200, data))
        await mock_entity.async_update()

    assert mock_entity.native_value == 2
