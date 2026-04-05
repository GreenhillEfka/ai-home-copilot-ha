"""Projection Contract Tests for remaining 7 untested sensors.

Sensors: area_presence_sensor_factory, habitus_zone_sensor, heat_pump_sensor,
neuron_dashboard, notification_sensor, onboarding_sensor, tariff_sensor.
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


def make_coord(**kwargs):
    c = MagicMock()
    c.data = kwargs
    return c


def make_core_coord():
    c = MagicMock()
    c._core_base_url = lambda: "http://core:8765"
    c._core_headers = lambda: {"Authorization": "Bearer test"}
    return c


# ─── area_presence_sensor_factory ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_area_presence_sensor_factory_ha_lokal():
    from custom_components.copilot_ha.sensors.area_presence_sensor_factory import AreaPresenceSensorFactory
    coord = make_coord(areas={})
    sensor = AreaPresenceSensorFactory(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── habitus_zone_sensor ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_habitus_zone_sensor_ha_lokal():
    from custom_components.copilot_ha.sensors.habitus_zone_sensor import HabitusZoneSensor
    coord = make_coord(active_zone="living_room", confidence=0.92)
    sensor = HabitusZoneSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


@pytest.mark.asyncio
async def test_habitus_zone_sensor_state():
    from custom_components.copilot_ha.sensors.habitus_zone_sensor import HabitusZoneSensor
    coord = make_coord(active_zone="kitchen", confidence=0.95)
    sensor = HabitusZoneSensor(coord)
    attrs = sensor.extra_state_attributes
    assert attrs["active_zone"] == "kitchen"


# ─── heat_pump_sensor (Core-API) ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_heat_pump_sensor_200():
    from custom_components.copilot_ha.sensors.heat_pump_sensor import HeatPumpSensor
    data = {"ok": True, "cop": 4.2, "flow_temp_c": 45, "power_kw": 8.5}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = HeatPumpSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    attrs = sensor.extra_state_attributes
    assert attrs["cop"] == 4.2


@pytest.mark.asyncio
async def test_heat_pump_sensor_404():
    from custom_components.copilot_ha.sensors.heat_pump_sensor import HeatPumpSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = HeatPumpSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── neuron_dashboard (CoordinatorEntity) ───────────────────────────────────────
@pytest.mark.asyncio
async def test_neuron_dashboard_ha_lokal():
    from custom_components.copilot_ha.sensors.neuron_dashboard import NeuronDashboardSensor
    coord = make_coord(active_neurons=48, total_synapses=312)
    sensor = NeuronDashboardSensor(coord)
    assert not hasattr(sensor, '_core_base_url')


# ─── notification_sensor (Core-API) ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_notification_sensor_200():
    from custom_components.copilot_ha.sensors.notification_sensor import NotificationSensor
    data = {"ok": True, "priority": 1, "messages": ["Energie sparen"]}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = NotificationSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 1


@pytest.mark.asyncio
async def test_notification_sensor_404():
    from custom_components.copilot_ha.sensors.notification_sensor import NotificationSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = NotificationSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── onboarding_sensor (Core-API) ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_onboarding_sensor_200():
    from custom_components.copilot_ha.sensors.onboarding_sensor import OnboardingSensor
    data = {"ok": True, "completed_steps": 4, "total_steps": 8}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = OnboardingSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == "50%"


@pytest.mark.asyncio
async def test_onboarding_sensor_404():
    from custom_components.copilot_ha.sensors.onboarding_sensor import OnboardingSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = OnboardingSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()


# ─── tariff_sensor (Core-API) ──────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_tariff_sensor_200():
    from custom_components.copilot_ha.sensors.tariff_sensor import TariffSensor
    data = {"ok": True, "current_eur_kwh": 0.28, "currency": "EUR", "period": "peak"}
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(200, data))
        sensor = TariffSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
    assert sensor.native_value == 0.28


@pytest.mark.asyncio
async def test_tariff_sensor_404():
    from custom_components.copilot_ha.sensors.tariff_sensor import TariffSensor
    with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession") as mock_fn:
        mock_fn.return_value = FakeSession(FakeResp(404))
        sensor = TariffSensor(make_core_coord())
        sensor.hass = MagicMock()
        await sensor.async_update()
