"""Tests for the final untested PilotSuite HA sensor families (7 sensors).

Covers sensor setup/update behavior for the remaining uncovered modules:
- area_presence_sensor_factory
- habitus_zone_sensor
- heat_pump_sensor
- neuron_dashboard
- notification_sensor
- onboarding_sensor
- tariff_sensor
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.copilot_ha.habitus_zones_store_v2 import HabitusZoneV2
from custom_components.copilot_ha.sensors.area_presence_sensor_factory import (
    async_build_area_presence_sensors,
)
from custom_components.copilot_ha.sensors.habitus_zone_sensor import HabitusZoneSensor
from custom_components.copilot_ha.sensors.heat_pump_sensor import HeatPumpSensor
from custom_components.copilot_ha.sensors.neuron_dashboard import (
    NeuronDashboardSensor,
)
from custom_components.copilot_ha.sensors.notification_sensor import NotificationSensor
from custom_components.copilot_ha.sensors.onboarding_sensor import OnboardingSensor
from custom_components.copilot_ha.sensors.tariff_sensor import TariffSensor


@dataclass
class _FakeState:
    entity_id: str
    state: str
    attributes: dict[str, Any]


class _FakeStates:
    def __init__(
        self,
        states: dict[str, _FakeState],
        persons: list[_FakeState],
    ) -> None:
        self._states = states
        self._persons = persons

    def get(self, entity_id: str) -> _FakeState | None:
        return self._states.get(entity_id)

    def async_all(self, domain: str):
        if domain == "person":
            return self._persons
        return []


class _FakeHass:
    def __init__(
        self,
        states: dict[str, _FakeState],
        persons: list[_FakeState],
    ) -> None:
        self.states = _FakeStates(states, persons)


class _FakeResponse:
    def __init__(self, status: int, payload: Any) -> None:
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return None

    async def json(self) -> Any:
        return self._payload


class _FakeSession:
    def __init__(self, routes: dict[str, tuple[int, Any]]) -> None:
        self.routes = routes
        self.calls: list[str] = []

    def get(self, url: str, *_, **__) -> _FakeResponse:
        self.calls.append(url)
        for marker, (status, payload) in self.routes.items():
            if marker in url:
                return _FakeResponse(status, payload)
        return _FakeResponse(404, {"ok": False})


def _coordinator_with(*, session=None, config: dict[str, Any] | None = None, data: dict[str, Any] | None = None):
    coordinator = MagicMock()
    coordinator._config = {
        "host": "core.local",
        "port": 8909,
        "token": "sekret",
        **(config or {}),
    }
    coordinator.api = MagicMock(_active_base_url="http://core.local:8909")
    coordinator._session = session
    coordinator.data = data or {}
    return coordinator


@pytest.mark.asyncio
async def test_area_presence_factory_extracts_sources_for_motion_zone():
    hass = _FakeHass(
        states={
            "binary_sensor.mmwave_front": _FakeState(
                entity_id="binary_sensor.mmwave_front",
                state="on",
                attributes={"device_class": "presence"},
            ),
            "binary_sensor.pir_front": _FakeState(
                entity_id="binary_sensor.pir_front",
                state="off",
                attributes={"device_class": "motion"},
            ),
            "device_tracker.phone_alice": _FakeState(
                entity_id="device_tracker.phone_alice",
                state="home",
                attributes={"source_type": "bluetooth"},
            ),
            "person.alice": _FakeState(
                entity_id="person.alice",
                state="home",
                attributes={"area_id": "bereich_wohnzimmer", "zone": "zone:wohnzimmer"},
            ),
        },
        persons=[
            _FakeState(
                entity_id="person.alice",
                state="home",
                attributes={"area_id": "bereich_wohnzimmer", "zone": "zone:wohnzimmer"},
            )
        ],
    )

    zone = HabitusZoneV2(
        zone_id="zone:wohnzimmer",
        name="Wohnzimmer",
        entities={
            "motion": ["binary_sensor.mmwave_front", "binary_sensor.pir_front"],
            "other": ["light.something"],
        },
        entity_ids=(
            "binary_sensor.mmwave_front",
            "binary_sensor.pir_front",
            "device_tracker.phone_alice",
        ),
        metadata={"ha_area_ids": ["bereich_wohnzimmer"]},
    )
    coordinator = _coordinator_with()

    with patch(
        "custom_components.copilot_ha.sensors.area_presence_sensor_factory.async_get_zones_v2",
        AsyncMock(return_value=[zone]),
    ):
        sensors = await async_build_area_presence_sensors(hass, "entry_1", coordinator, None)

    assert len(sensors) == 1
    sensor = sensors[0]
    assert sensor._mmwave_entities == ["binary_sensor.mmwave_front"]
    assert sensor._motion_entities == ["binary_sensor.pir_front"]
    assert sensor._ble_entities == ["device_tracker.phone_alice"]
    assert sensor._person_entities == ["person.alice"]


@pytest.mark.asyncio
async def test_area_presence_factory_skips_zone_without_presence_sources():
    hass = _FakeHass(states={}, persons=[])
    zone = HabitusZoneV2(
        zone_id="zone:technik",
        name="Technik",
        entities={"lock": ["lock.frontaleite"]},
        entity_ids=("lock.frontaleite",),
    )
    coordinator = _coordinator_with()

    with patch(
        "custom_components.copilot_ha.sensors.area_presence_sensor_factory.async_get_zones_v2",
        AsyncMock(return_value=[zone]),
    ):
        sensors = await async_build_area_presence_sensors(hass, "entry_1", coordinator, None)

    assert sensors == []


@pytest.mark.asyncio
async def test_habitus_zone_sensor_reads_hub_zones_path_and_formats_state():
    coordinator = _coordinator_with()
    sensor = HabitusZoneSensor(coordinator)
    sensor.hass = MagicMock()

    payload = {
        "total_zones": 2,
        "active_zones": 1,
        "total_rooms": 8,
        "total_entities": 42,
        "modes": {"party": 0, "sleeping": 1},
        "zones": [{"name": "Wohnzimmer", "mode": "sleeping", "room_count": 2, "entity_count": 4}],
    }

    with patch.object(sensor, "_fetch", AsyncMock(return_value=payload)) as fetch:
        await sensor.async_update()
        fetch.assert_awaited_once_with("/api/v1/hub/zones")

    assert sensor.state == "1/2 aktiv"
    assert sensor.icon == "mdi:sleep"
    assert sensor.extra_state_attributes["total_zones"] == 2
    assert sensor.extra_state_attributes["zones"][0]["name"] == "Wohnzimmer"


@pytest.mark.asyncio
async def test_notification_sensor_loads_notifications_and_digest():
    session = _FakeSession(
        {
            "/api/v1/notifications?limit=10": (
                200,
                {
                    "ok": True,
                    "count": 3,
                    "notifications": [
                        {"title": "Update", "level": "info"},
                        {"title": "Alarm", "level": "warn"},
                    ],
                },
            ),
            "/api/v1/notifications/digest?hours=24": (
                200,
                {
                    "ok": True,
                    "count": 9,
                    "by_source": {"system": 5, "weather": 4},
                    "by_priority": {"info": 6, "high": 3},
                },
            ),
        }
    )
    coordinator = _coordinator_with(session=session)
    sensor = NotificationSensor(coordinator)
    sensor.hass = MagicMock()

    await sensor.async_update()

    assert sensor.native_value == "3 pending"
    assert sensor.icon == "mdi:bell-alert"
    assert sensor.extra_state_attributes["pending_count"] == 3
    assert sensor.extra_state_attributes["digest_count"] == 9
    assert sensor.extra_state_attributes["notifications_url"].endswith("/api/v1/notifications")


@pytest.mark.asyncio
async def test_onboarding_sensor_loads_onboarding_status():
    session = _FakeSession(
        {
            "/api/v1/onboarding/state": (
                200,
                {
                    "ok": True,
                    "current_step": 0,
                    "total_steps": 4,
                    "agent_name": "Styx",
                    "is_complete": False,
                    "steps": [
                        {"title": "Start", "completed": True},
                        {"title": "Configure", "completed": False},
                    ],
                },
            )
        }
    )
    coordinator = _coordinator_with(session=session)
    sensor = OnboardingSensor(coordinator)
    sensor.hass = MagicMock()

    with patch(
        "custom_components.copilot_ha.sensors.onboarding_sensor.async_get_clientsession",
        return_value=session,
    ):
        await sensor.async_update()

    assert sensor.native_value == "Schritt 1/4"
    assert sensor.icon == "mdi:school"
    assert sensor.extra_state_attributes["current_step"] == 0
    assert sensor.extra_state_attributes["completed_steps"] == 1


@pytest.mark.asyncio
async def test_tariff_sensor_loads_regional_summary_and_maps_to_attributes():
    session = _FakeSession(
        {
            "/api/v1/regional/tariff/summary": (
                200,
                {
                    "ok": True,
                    "current_price_ct_kwh": 24.5,
                    "current_price_eur_kwh": 0.245,
                    "current_level": "low",
                    "avg_price_eur_kwh": 0.27,
                    "min_price_eur_kwh": 0.12,
                    "max_price_eur_kwh": 0.91,
                    "min_hour": "02:00",
                    "max_hour": "18:00",
                    "spread_eur_kwh": 0.79,
                    "tariff_type": "region-reg",
                    "source": "regional-service",
                    "hours_available": 24,
                },
            )
        }
    )
    coordinator = _coordinator_with(session=session)
    sensor = TariffSensor(coordinator)
    sensor.hass = MagicMock()

    with patch(
        "custom_components.copilot_ha.sensors.tariff_sensor.async_get_clientsession",
        return_value=session,
    ):
        await sensor.async_update()

    assert sensor.native_value == 24.5
    assert sensor.icon == "mdi:flash"
    assert sensor.extra_state_attributes["avg_price_ct_kwh"] == 27.0
    assert sensor.extra_state_attributes["spread_ct_kwh"] == 79.0


@pytest.mark.asyncio
async def test_heat_pump_sensor_loads_status_and_schedule_from_regional_endpoint():
    session = _FakeSession(
        {
            "/api/v1/regional/heatpump/status": (
                200,
                {
                    "ok": True,
                    "current_cop": 2.9,
                    "current_action": "heat",
                    "current_power_kw": 5.2,
                    "room_temp_c": 21.5,
                    "target_room_temp_c": 22,
                    "current_level": "high",
                    "hot_water_temp_c": 48,
                },
            ),
            "/api/v1/regional/heatpump/schedule": (
                200,
                {
                    "ok": True,
                    "total_heat_kwh": 12.5,
                    "total_electricity_kwh": 19.4,
                    "total_cost_eur": 7.22,
                    "avg_cop": 3.1,
                    "runtime_hours": 4.7,
                    "dhw_cycles": 2,
                    "defrost_hours": 0.2,
                },
            ),
        }
    )
    coordinator = _coordinator_with(session=session)
    sensor = HeatPumpSensor(coordinator)
    sensor.hass = MagicMock()

    with patch(
        "custom_components.copilot_ha.sensors.heat_pump_sensor.async_get_clientsession",
        return_value=session,
    ):
        await sensor.async_update()

    assert sensor.native_value == 2.9
    assert sensor.icon == "mdi:heat-pump"
    attrs = sensor.extra_state_attributes
    assert attrs["total_heat_kwh"] == 12.5
    assert attrs["runtime_hours"] == 4.7


def test_neuron_dashboard_groups_neurons_by_category():
    coordinator = _coordinator_with(
        data={
            "neurons": {
                "time.daytime": {"active": True},
                "presence.home": {"active": False},
                "mood.chill": {"active": True},
                "climate.control": {"active": True},
                "random": "x",
            }
        }
    )
    sensor = NeuronDashboardSensor(coordinator)

    attrs = sensor.extra_state_attributes
    assert attrs["total_count"] == 5
    assert attrs["active_count"] == 3
    assert "time.daytime" in attrs["context_neurons"]
    assert "presence.home" in attrs["context_neurons"]
    assert "mood.chill" in attrs["mood_neurons"]
    assert attrs["state_neurons"]["climate.control"] == {"active": True}
