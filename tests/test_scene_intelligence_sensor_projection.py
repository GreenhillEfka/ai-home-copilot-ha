"""Projection Contract Tests for scene_intelligence_sensor.

Verifies: Core-API sensor — gracefully handles 404 when /hub/scenes missing.
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


@pytest.fixture
def make_sensor():
    from custom_components.copilot_ha.sensors.scene_intelligence_sensor import SceneIntelligenceSensor
    def _make(data=None, status=404):
        coordinator = MagicMock()
        coordinator._core_base_url = lambda: "http://core:8765"
        coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
        sensor = SceneIntelligenceSensor(coordinator)
        sensor.hass = MagicMock()
        if data:
            with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
                mock_fn.return_value = FakeSession(FakeResp(status, data))
                import asyncio
                asyncio.run(sensor.async_update())
        return sensor
    return _make


def test_scene_intelligence_sensor_200():
    """Core returns 200 — parses active scene."""
    from custom_components.copilot_ha.sensors.scene_intelligence_sensor import SceneIntelligenceSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    data = {
        "ok": True,
        "total_scenes": 8,
        "learned_patterns": 3,
        "active_scene": {"scene_id": "morning_routine", "name_de": "Morning Routine"}
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = SceneIntelligenceSensor(coordinator)
        sensor.hass = MagicMock()
        import asyncio
        asyncio.run(sensor.async_update())
    assert sensor.native_value == "Morning Routine"
    attrs = sensor.extra_state_attributes
    assert attrs["total_scenes"] == 8


def test_scene_intelligence_sensor_404():
    """Core returns 404 — gracefully degrades to 'Nicht verfügbar'."""
    from custom_components.copilot_ha.sensors.scene_intelligence_sensor import SceneIntelligenceSensor
    coordinator = MagicMock()
    coordinator._core_base_url = lambda: "http://core:8765"
    coordinator._core_headers = lambda: {"Authorization": "Bearer test"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = SceneIntelligenceSensor(coordinator)
        sensor.hass = MagicMock()
        import asyncio
        asyncio.run(sensor.async_update())
    # Default state when no data
    assert "verfügbar" in str(sensor.native_value)
