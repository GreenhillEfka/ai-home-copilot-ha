"""Batch Projection Tests for voice_context, inspector_sensor, media_follow sensors.

Tests verify HA-lokal (coordinator-only) and Core-API sensors.
"""
import pytest
from unittest.mock import MagicMock


# ─── voice_context_sensor ──────────────────────────────────────────────────────
def make_coord(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


@pytest.mark.asyncio
async def test_voice_context_ha_lokal():
    """VoiceContextSensor is CoordinatorEntity — HA-lokal."""
    from custom_components.copilot_ha.sensors.voice_context import VoiceContextSensor
    coord = make_coord(
        active_turns=3, conversation_id="abc",
        session_context={"topic": "energy"}
    )
    sensor = VoiceContextSensor(coord)
    assert sensor._attr_native_value == "ok"
    attrs = sensor.extra_state_attributes
    assert attrs["active_turns"] == 3


# ─── inspector_sensor ───────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_inspector_sensor_ha_lokal():
    """InspectorSensor is CoordinatorEntity — HA-lokal."""
    from custom_components.copilot_ha.sensors.inspector_sensor import InspectorSensor
    coord = make_coord(zones=5, tags=12, character={"mood": "productive"})
    sensor = InspectorSensor(coord, "zones", "Habitus Zones", "mdi:floor-plan")
    assert sensor.native_value == 5
    attrs = sensor.extra_state_attributes
    assert attrs["label"] == "Habitus Zones"


# ─── media_follow_sensor ────────────────────────────────────────────────────────
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


@pytest.mark.asyncio
async def test_media_follow_sensor_core_api():
    """MediaFollowSensor has Core-API dependency — test 200 parsing."""
    from custom_components.copilot_ha.sensors.media_follow_sensor import MediaFollowSensor
    coord = MagicMock()
    coord._core_base_url = lambda: "http://core:8765"
    coord._core_headers = lambda: {"Authorization": "Bearer test"}
    from unittest.mock import patch
    data = {"ok": True, "following": True, "media_title": "Jazz", "speaker": "Living Room"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = MediaFollowSensor(coord)
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "following"


@pytest.mark.asyncio
async def test_media_follow_sensor_404():
    """MediaFollowSensor 404 → graceful degradation."""
    from custom_components.copilot_ha.sensors.media_follow_sensor import MediaFollowSensor
    coord = MagicMock()
    coord._core_base_url = lambda: "http://core:8765"
    coord._core_headers = lambda: {"Authorization": "Bearer test"}
    from unittest.mock import patch
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = MediaFollowSensor(coord)
        sensor.hass = MagicMock()
        await sensor.async_update()
    # No crash
