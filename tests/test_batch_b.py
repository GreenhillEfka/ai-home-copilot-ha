"""Projection Contract Tests for remaining sensors (batch B).

Covers: mood_sensor, scene_intelligence, notification_intelligence,
presence_intelligence, hub_dashboard, system_integration, proactive_alert.
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


def make_coord(**kw):
    c = MagicMock()
    c.data = kw
    return c


def make_core_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── mood_sensor ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_mood_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.mood_sensor import MoodSensor
    sensor = MoodSensor(make_coord(mood="productive", mood_score=0.78))
    assert not hasattr(sensor, '_core_base_url')
    assert sensor.native_value == "productive"


# ─── scene_intelligence_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_scene_intelligence_sensor_200():
    from custom_components.copilot_ha.sensors.scene_intelligence_sensor import SceneIntelligenceSensor
    data = {"ok": True, "total_scenes": 8, "active_scene": {"scene_id": "morning_routine", "name_de": "Morning"}}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = SceneIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert "Morning" in str(sensor.native_value)


@pytest.mark.asyncio
async def test_scene_intelligence_sensor_404():
    from custom_components.copilot_ha.sensors.scene_intelligence_sensor import SceneIntelligenceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = SceneIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── notification_intelligence_sensor ───────────────────────────────────────────
@pytest.mark.asyncio
async def test_notification_intelligence_sensor_200():
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
    data = {"ok": True, "priority": 1, "count": 3}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = NotificationIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["count"] == 3


@pytest.mark.asyncio
async def test_notification_intelligence_sensor_404():
    from custom_components.copilot_ha.sensors.notification_intelligence_sensor import NotificationIntelligenceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = NotificationIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── presence_intelligence_sensor ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_presence_intelligence_sensor_200():
    from custom_components.copilot_ha.sensors.presence_intelligence_sensor import PresenceIntelligenceSensor
    data = {"ok": True, "primary_person": "Andreas", "confidence": 0.92}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = PresenceIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "Andreas"


@pytest.mark.asyncio
async def test_presence_intelligence_sensor_404():
    from custom_components.copilot_ha.sensors.presence_intelligence_sensor import PresenceIntelligenceSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = PresenceIntelligenceSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── hub_dashboard_sensor ──────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_hub_dashboard_sensor_200():
    from custom_components.copilot_ha.sensors.hub_dashboard_sensor import HubDashboardSensor
    data = {"ok": True, "summary": "All systems operational", "active_modules": 4}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = HubDashboardSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs.get("active_modules") == 4


@pytest.mark.asyncio
async def test_hub_dashboard_sensor_404():
    from custom_components.copilot_ha.sensors.hub_dashboard_sensor import HubDashboardSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(404))
        sensor = HubDashboardSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── system_integration_sensor ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_system_integration_sensor_200():
    from custom_components.copilot_ha.sensors.system_integration_sensor import SystemIntegrationSensor
    data = {"ok": True, "integrations": 12, "status": "healthy"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = SystemIntegrationSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 12


# ─── proactive_alert_sensor ────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_proactive_alert_sensor_200():
    from custom_components.copilot_ha.sensors.proactive_alert_sensor import ProactiveAlertSensor
    data = {"ok": True, "alerts": 2, "critical": 0}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as m:
        m.return_value = FakeSession(FakeResp(200, data))
        sensor = ProactiveAlertSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 2
