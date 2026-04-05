"""Projection Contract Tests for notification_intelligence and presence_intelligence sensors.

Both are Core-API sensors. Tests verify 200 parsing and 404 graceful degradation.
"""
import pytest
from unittest.mock import MagicMock, patch
import asyncio


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


# ─── notification_intelligence_sensor ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_notification_intelligence_sensor_200():
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
    data = {
        "ok": True, "priority": 1, "count": 3,
        "last_message": "Energie sparen", "category": "energy"
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        coord = make_coord()
        sensor = NotificationIntelligenceSensor(coord)
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["count"] == 3


@pytest.mark.asyncio
async def test_notification_intelligence_sensor_404():
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = NotificationIntelligenceSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    # Graceful degradation — no crash


# ─── presence_intelligence_sensor ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_presence_intelligence_sensor_200():
    from custom_components.copilot_ha.sensors.presence_intelligence_sensor import PresenceIntelligenceSensor
    data = {
        "ok": True, "primary_person": "Andreas",
        "confidence": 0.92, "location": "living_room"
    }
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = PresenceIntelligenceSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "Andreas"
    attrs = sensor.extra_state_attributes
    assert attrs["confidence"] == 0.92


@pytest.mark.asyncio
async def test_presence_intelligence_sensor_404():
    from custom_components.copilot_ha.sensors.presence_intelligence_sensor import PresenceIntelligenceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = PresenceIntelligenceSensor(make_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    # Graceful degradation — no crash
