"""Projection Contract Tests for comfort_index_sensor (HA-83/HA-88).

Verifies: Sensor degrades gracefully when Core /comfort endpoint is missing.
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
    from custom_components.copilot_ha.sensors.comfort_index_sensor import ComfortIndexSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    coordinator._session = FakeSession(FakeResp(404))
    entity = ComfortIndexSensor(coordinator)
    entity.hass = MagicMock()
    return entity


@pytest.mark.asyncio
async def test_comfort_index_200():
    """Core returns 200 — sensor parses score and grade."""
    from custom_components.copilot_ha.sensors.comfort_index_sensor import ComfortIndexSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {
        "ok": True, "score": 87.5, "grade": "A",
        "zone_id": "living_room", "suggestions": ["Open blinds"],
        "readings": [{"factor": "temperature", "score": 90, "status": "optimal", "raw_value": 21.5}]
    }
    coordinator._session = FakeSession(FakeResp(200, data))
    entity = ComfortIndexSensor(coordinator)
    await entity.async_update()
    assert entity.native_value == 87.5
    attrs = entity.extra_state_attributes
    assert attrs["grade"] == "A"
    assert attrs["temperature_score"] == 90


@pytest.mark.asyncio
async def test_comfort_index_404_degrades_gracefully(mock_entity):
    """Core returns 404 — sensor state=None, no exception."""
    await mock_entity.async_update()
    assert mock_entity.native_value is None
    assert mock_entity.icon == "mdi:home-thermometer"


@pytest.mark.asyncio
async def test_comfort_index_no_session(mock_entity):
    """No session available — graceful degradation."""
    mock_entity.coordinator._session = None
    await mock_entity.async_update()
    assert mock_entity.native_value is None
