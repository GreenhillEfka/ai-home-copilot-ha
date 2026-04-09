"""Builder contract tests for area_presence_sensor_factory.py.

Verifies the factory is a pure HA-side builder shell on Habitus zone metadata:
- motion role splits into mmWave vs. PIR by device_class
- BLE trackers come only from bluetooth device_trackers in the zone
- person discovery matches home persons to the zone's HA areas
- zones without any discovered sources are skipped

HA-253
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.pilotsuite.habitus_zones_store_v2 import HabitusZoneV2
from custom_components.pilotsuite.sensors import area_presence_sensor_factory as factory


class MockState:
    """Minimal HA State-like object for factory tests."""

    def __init__(self, entity_id: str, state: str = "off", attributes: dict | None = None) -> None:
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class FakeStates:
    """Minimal hass.states facade."""

    def __init__(self, states: list[MockState]) -> None:
        self._by_id = {state.entity_id: state for state in states}
        self._all = list(states)

    def get(self, entity_id: str):
        return self._by_id.get(entity_id)

    def async_all(self, domain: str | None = None):
        if domain is None:
            return list(self._all)
        prefix = f"{domain}."
        return [state for state in self._all if state.entity_id.startswith(prefix)]


class DummyAreaPresenceSensor:
    """Capture constructor args without importing the real binary sensor."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.zone_id = kwargs["zone_id"]
        self.zone_name = kwargs["zone_name"]
        self.mmwave_entities = kwargs["mmwave_entities"]
        self.motion_entities = kwargs["motion_entities"]
        self.ble_entities = kwargs["ble_entities"]
        self.person_entities = kwargs["person_entities"]


# ─────────────────────────────────────────────────────────────────────────────
# Helper contract tests
# ─────────────────────────────────────────────────────────────────────────────


def test_apf1_split_mmwave_motion_sorts_presence_vs_motion_and_unknown() -> None:
    hass = SimpleNamespace(
        states=FakeStates(
            [
                MockState("binary_sensor.mmwave_sofa", attributes={"device_class": "presence"}),
                MockState("binary_sensor.pir_hall", attributes={"device_class": "motion"}),
                MockState("binary_sensor.legacy", attributes={"device_class": "vibration"}),
                MockState("binary_sensor.blank", attributes={}),
            ]
        )
    )

    mmwave, motion = asyncio.run(
        factory._split_mmwave_motion(
            hass,
            [
                "binary_sensor.mmwave_sofa",
                "binary_sensor.pir_hall",
                "binary_sensor.legacy",
                "binary_sensor.blank",
            ],
        )
    )

    assert mmwave == ["binary_sensor.mmwave_sofa"]
    assert motion == [
        "binary_sensor.pir_hall",
        "binary_sensor.legacy",
        "binary_sensor.blank",
    ]


def test_apf2_split_mmwave_motion_skips_missing_entities() -> None:
    hass = SimpleNamespace(states=FakeStates([]))

    mmwave, motion = asyncio.run(
        factory._split_mmwave_motion(
            hass,
            ["binary_sensor.missing_presence", "binary_sensor.missing_motion"],
        )
    )

    assert mmwave == []
    assert motion == []


def test_apf3_discover_ble_trackers_only_returns_zone_bluetooth_trackers() -> None:
    zone = HabitusZoneV2(
        zone_id="zone:wohnzimmer",
        name="Wohnzimmer",
        entity_ids=(
            "device_tracker.phone_alice",
            "device_tracker.phone_bob",
            "binary_sensor.motion_sofa",
        ),
        entities={
            "motion": ("binary_sensor.motion_sofa",),
            "other": ("device_tracker.watch_alice",),
        },
    )
    hass = SimpleNamespace(
        states=FakeStates(
            [
                MockState("device_tracker.phone_alice", "home", {"source_type": "bluetooth"}),
                MockState("device_tracker.phone_bob", "home", {"source_type": "router"}),
                MockState("device_tracker.watch_alice", "home", {"source_type": "bluetooth"}),
                MockState("binary_sensor.motion_sofa", "on", {"device_class": "motion"}),
            ]
        )
    )

    ble = asyncio.run(factory._discover_ble_trackers(hass, zone))

    assert set(ble) == {"device_tracker.phone_alice", "device_tracker.watch_alice"}


def test_apf4_discover_persons_matches_home_persons_by_zone_and_area() -> None:
    zone = HabitusZoneV2(
        zone_id="zone:wohnzimmer",
        name="Wohnzimmer",
        metadata={"ha_area_ids": ["wohnzimmer", "living_room"]},
    )
    hass = SimpleNamespace(
        states=FakeStates(
            [
                MockState("person.alice", "home", {"zone": "Wohnzimmer"}),
                MockState("person.bob", "home", {"area_id": "living_room"}),
                MockState("person.carol", "away", {"zone": "Wohnzimmer"}),
                MockState("person.dave", "home", {"zone": "Kueche"}),
            ]
        )
    )

    persons = asyncio.run(factory._discover_persons_for_zone(hass, zone))

    assert persons == ["person.alice", "person.bob"]


# ─────────────────────────────────────────────────────────────────────────────
# Factory builder tests
# ─────────────────────────────────────────────────────────────────────────────


def test_apf5_build_returns_empty_when_no_zones(monkeypatch) -> None:
    async def fake_get_zones_v2(hass, entry_id):
        return []

    monkeypatch.setattr(factory, "async_get_zones_v2", fake_get_zones_v2)
    monkeypatch.setattr(factory, "_get_area_presence_sensor_class", lambda: DummyAreaPresenceSensor)

    sensors = asyncio.run(
        factory.async_build_area_presence_sensors(
            hass=SimpleNamespace(states=FakeStates([])),
            entry_id="entry-1",
            coordinator=object(),
            entry=object(),
        )
    )

    assert sensors == []


def test_apf6_build_creates_sensor_with_split_ble_and_person_sources(monkeypatch) -> None:
    zone = HabitusZoneV2(
        zone_id="zone:wohnzimmer",
        name="Wohnzimmer",
        entity_ids=("device_tracker.phone_alice",),
        entities={
            "motion": (
                "binary_sensor.mmwave_sofa",
                "binary_sensor.motion_hall",
            ),
            "media": ("binary_sensor.motion_tv",),
            "door": ("binary_sensor.front_door",),
        },
        metadata={"ha_area_ids": ["wohnzimmer"]},
    )
    hass = SimpleNamespace(
        states=FakeStates(
            [
                MockState("binary_sensor.mmwave_sofa", "on", {"device_class": "presence"}),
                MockState("binary_sensor.motion_hall", "off", {"device_class": "motion"}),
                MockState("binary_sensor.motion_tv", "on", {"device_class": "motion"}),
                MockState("binary_sensor.front_door", "off", {"device_class": "door"}),
                MockState("device_tracker.phone_alice", "home", {"source_type": "bluetooth"}),
                MockState("person.alice", "home", {"zone": "Wohnzimmer"}),
                MockState("person.bob", "away", {"zone": "Wohnzimmer"}),
            ]
        )
    )

    async def fake_get_zones_v2(hass, entry_id):
        return [zone]

    monkeypatch.setattr(factory, "async_get_zones_v2", fake_get_zones_v2)
    monkeypatch.setattr(factory, "_get_area_presence_sensor_class", lambda: DummyAreaPresenceSensor)

    sensors = asyncio.run(
        factory.async_build_area_presence_sensors(
            hass=hass,
            entry_id="entry-1",
            coordinator="coord",
            entry="entry-obj",
        )
    )

    assert len(sensors) == 1
    sensor = sensors[0]
    assert sensor.zone_id == "wohnzimmer"
    assert sensor.zone_name == "Wohnzimmer"
    assert sensor.mmwave_entities == ["binary_sensor.mmwave_sofa"]
    assert sensor.motion_entities == ["binary_sensor.motion_hall", "binary_sensor.motion_tv"]
    assert sensor.ble_entities == ["device_tracker.phone_alice"]
    assert sensor.person_entities == ["person.alice"]


def test_apf7_build_skips_zone_without_any_sources(monkeypatch) -> None:
    zone = HabitusZoneV2(
        zone_id="zone:leer",
        name="Leer",
        entities={"door": ("binary_sensor.front_door",)},
        metadata={"ha_area_ids": ["leer"]},
    )
    hass = SimpleNamespace(
        states=FakeStates(
            [
                MockState("binary_sensor.front_door", "off", {"device_class": "door"}),
                MockState("person.alice", "away", {"zone": "Leer"}),
            ]
        )
    )

    async def fake_get_zones_v2(hass, entry_id):
        return [zone]

    monkeypatch.setattr(factory, "async_get_zones_v2", fake_get_zones_v2)
    monkeypatch.setattr(factory, "_get_area_presence_sensor_class", lambda: DummyAreaPresenceSensor)

    sensors = asyncio.run(
        factory.async_build_area_presence_sensors(
            hass=hass,
            entry_id="entry-1",
            coordinator="coord",
            entry="entry-obj",
        )
    )

    assert sensors == []


# ─────────────────────────────────────────────────────────────────────────────
# Global contract guards
# ─────────────────────────────────────────────────────────────────────────────


def test_gc1_factory_targets_zone_store_and_presence_discovery_pipeline() -> None:
    src = open("custom_components/pilotsuite/sensors/area_presence_sensor_factory.py").read()
    assert "async_get_zones_v2" in src
    assert "_split_mmwave_motion" in src
    assert "_discover_ble_trackers" in src
    assert "_discover_persons_for_zone" in src
    assert "zone.zone_id.replace(\"zone:\", \"\")" in src


def test_gc2_factory_skips_zones_without_discovered_presence_sources() -> None:
    src = open("custom_components/pilotsuite/sensors/area_presence_sensor_factory.py").read()
    assert "if not has_sources:" in src
    assert "continue" in src
    assert "role == \"motion\"" in src
    assert "elif role in (\"door\", \"window\", \"lock\")" in src
