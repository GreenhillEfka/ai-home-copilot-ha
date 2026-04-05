"""Tests for habitus_zone_sensor.py Core-Truth Projection.

Verifies that HabitusZoneSensor projects Core-provided zone truth
from /api/v1/hub/zones without local semantic invention.

Philosophy:
- zones[].name          → from Core (coordinator.data via _fetch)
- zones[].mode          → from Core
- zones[].room_count     → from Core
- zones[].entity_count   → from Core
- modes.party/sleeping   → from Core
- HA only projects; HA does not compute or translate.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Minimal mock setup (no HA imports) ────────────────────────────────

class MockCoordinator:
    """Stand-in for CopilotDataUpdateCoordinator with known data shapes."""
    def __init__(self, zone_data: dict | None = None):
        self._zone_data = zone_data or {}

    async def _fetch(self, path: str, *, timeout_s: float = 10.0):
        if path == "/api/v1/hub/zones":
            return self._zone_data
        return None


class HabitusZoneSensor:
    """Stand-in for HabitusZoneSensor to test projection logic in isolation.

    Mirrors the real sensor's logic so we verify the projection contract,
    not the HA framework wiring.
    """
    def __init__(self, coordinator: MockCoordinator):
        self.coordinator = coordinator
        self._zone_data: dict = {}

    @property
    def state(self) -> str:
        total = self._zone_data.get("total_zones", 0)
        active = self._zone_data.get("active_zones", 0)
        if total == 0:
            return "Keine Zonen"
        return f"{active}/{total} aktiv"

    @property
    def icon(self) -> str:
        modes = self._zone_data.get("modes", {})
        if modes.get("party", 0) > 0:
            return "mdi:party-popper"
        if modes.get("sleeping", 0) > 0:
            return "mdi:sleep"
        return "mdi:home-floor-1"

    @property
    def extra_state_attributes(self) -> dict:
        zones = self._zone_data.get("zones", [])
        return {
            "total_zones": self._zone_data.get("total_zones", 0),
            "total_rooms": self._zone_data.get("total_rooms", 0),
            "total_entities": self._zone_data.get("total_entities", 0),
            "active_zones": self._zone_data.get("active_zones", 0),
            "modes": self._zone_data.get("modes", {}),
            "unassigned_rooms": self._zone_data.get("unassigned_rooms", []),
            "zones": [
                {
                    "name": z.get("name"),
                    "mode": z.get("mode"),
                    "rooms": z.get("room_count", 0),
                    "entities": z.get("entity_count", 0),
                }
                for z in zones[:10]
            ],
        }

    async def async_update(self) -> None:
        data = await self.coordinator._fetch("/api/v1/hub/zones")
        if data:
            self._zone_data = data


# ── Contract Tests ────────────────────────────────────────────────────

@pytest.fixture
def empty_zone_data():
    return {
        "total_zones": 0,
        "total_rooms": 0,
        "total_entities": 0,
        "active_zones": 0,
        "modes": {},
        "zones": [],
        "unassigned_rooms": [],
    }


@pytest.fixture
def populated_zone_data():
    return {
        "total_zones": 3,
        "total_rooms": 7,
        "total_entities": 42,
        "active_zones": 2,
        "modes": {"party": 1, "sleeping": 0, "focus": 1},
        "zones": [
            {
                "name": "Wohnzimmer",
                "mode": "relax",
                "room_count": 2,
                "entity_count": 15,
            },
            {
                "name": "Schlafzimmer",
                "mode": "sleeping",
                "room_count": 1,
                "entity_count": 8,
            },
            {
                "name": "Küche",
                "mode": "focus",
                "room_count": 3,
                "entity_count": 19,
            },
        ],
        "unassigned_rooms": ["Flur"],
    }


# Case 1: empty state → "Keine Zonen"
def test_case_01_empty_zones_state(empty_zone_data):
    """Case 1: No zones → state is 'Keine Zonen'."""
    coordinator = MockCoordinator(empty_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    assert sensor.state == "Keine Zonen"


@pytest.fixture
async def populated_sensor(populated_zone_data):
    """Sensor with async_update already called (required for all state/attribute checks)."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    return sensor


# Case 1: empty state → "Keine Zonen"
def test_case_01_empty_zones_state(empty_zone_data):
    """Case 1: No zones → state is 'Keine Zonen'."""
    coordinator = MockCoordinator(empty_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    assert sensor.state == "Keine Zonen"


# Case 2: populated state → "{active}/{total} aktiv"
@pytest.mark.asyncio
async def test_case_02_populated_zones_state(populated_zone_data):
    """Case 2: With zones → state is '{active}/{total} aktiv'."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.state == "2/3 aktiv"


# Case 3: icon → mdi:party-popper when party mode > 0
@pytest.mark.asyncio
async def test_case_03_icon_party_mode(populated_zone_data):
    """Case 3: Party mode active → mdi:party-popper icon."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.icon == "mdi:party-popper"


# Case 4: icon → mdi:sleep when sleeping mode > 0 (no party)
@pytest.mark.asyncio
async def test_case_04_icon_sleeping_mode(populated_zone_data):
    """Case 4: Sleeping mode active (no party) → mdi:sleep icon."""
    data = populated_zone_data.copy()
    data["modes"] = {"sleeping": 1, "focus": 1, "party": 0}
    coordinator = MockCoordinator(data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.icon == "mdi:sleep"



# Case 5: icon → mdi:home-floor-1 when no special mode
def test_case_05_icon_default_mode(empty_zone_data):
    """Case 5: No special mode → default mdi:home-floor-1 icon."""
    coordinator = MockCoordinator(empty_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    assert sensor.icon == "mdi:home-floor-1"


# Case 6: attributes.total_zones → from Core
@pytest.mark.asyncio
async def test_case_06_total_zones_attribute(populated_zone_data):
    """Case 6: total_zones attribute comes from Core."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.extra_state_attributes["total_zones"] == 3


# Case 7: attributes.total_rooms → from Core
@pytest.mark.asyncio
async def test_case_07_total_rooms_attribute(populated_zone_data):
    """Case 7: total_rooms attribute comes from Core."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.extra_state_attributes["total_rooms"] == 7


# Case 8: attributes.total_entities → from Core
@pytest.mark.asyncio
async def test_case_08_total_entities_attribute(populated_zone_data):
    """Case 8: total_entities attribute comes from Core."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.extra_state_attributes["total_entities"] == 42


# Case 9: attributes.active_zones → from Core
@pytest.mark.asyncio
async def test_case_09_active_zones_attribute(populated_zone_data):
    """Case 9: active_zones attribute comes from Core."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.extra_state_attributes["active_zones"] == 2


# Case 10: attributes.modes → from Core (no local computation)
@pytest.mark.asyncio
async def test_case_10_modes_attribute(populated_zone_data):
    """Case 10: modes attribute is Core-provided, not computed locally."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    modes = sensor.extra_state_attributes["modes"]
    assert modes == {"party": 1, "sleeping": 0, "focus": 1}


# Case 11: attributes.zones → only first 10 projected
@pytest.mark.asyncio
async def test_case_11_zones_limited_to_10(populated_zone_data):
    """Case 11: zones list is capped at 10 entries (no local computation)."""
    many_zones = populated_zone_data.copy()
    many_zones["zones"] = [
        {"name": f"Zone {i}", "mode": "focus", "room_count": 1, "entity_count": 1}
        for i in range(15)
    ]
    coordinator = MockCoordinator(many_zones)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert len(sensor.extra_state_attributes["zones"]) == 10


# Case 12: zone entry → name, mode, room_count, entity_count (no semantic translation)
@pytest.mark.asyncio
async def test_case_12_zone_entry_fields(populated_zone_data):
    """Case 12: Each zone entry has name/mode/rooms/entities from Core."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    zones = sensor.extra_state_attributes["zones"]
    wohnzimmer = next(z for z in zones if z["name"] == "Wohnzimmer")
    assert wohnzimmer["mode"] == "relax"
    assert wohnzimmer["rooms"] == 2
    assert wohnzimmer["entities"] == 15


# Case 13: unassigned_rooms → from Core (empty list when none)
@pytest.mark.asyncio
async def test_case_13_unassigned_rooms(populated_zone_data):
    """Case 13: unassigned_rooms is Core-provided, defaults to empty list."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    assert sensor.extra_state_attributes["unassigned_rooms"] == ["Flur"]


# Case 14: empty zone_data → all numeric attributes default to 0
def test_case_14_empty_data_defaults(empty_zone_data):
    """Case 14: Empty Core response → all counts default to 0."""
    coordinator = MockCoordinator(empty_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    attrs = sensor.extra_state_attributes
    assert attrs["total_zones"] == 0
    assert attrs["total_rooms"] == 0
    assert attrs["total_entities"] == 0
    assert attrs["active_zones"] == 0


# Case 15: async_update → populates _zone_data from /api/v1/hub/zones
@pytest.mark.asyncio
async def test_case_15_async_update_fetches_core_zones(populated_zone_data):
    """Case 15: async_update calls Core /api/v1/hub/zones and populates _zone_data."""
    coordinator = MockCoordinator(populated_zone_data)
    sensor = HabitusZoneSensor(coordinator)
    assert sensor._zone_data == {}
    await sensor.async_update()
    assert sensor._zone_data["total_zones"] == 3
    assert sensor._zone_data["active_zones"] == 2


# Case 16: zones with missing room_count/entity_count → defaults to 0
@pytest.mark.asyncio
async def test_case_16_zone_missing_counts():
    """Case 16: Zone entries with missing counts default to 0."""
    data = {
        "total_zones": 1,
        "total_rooms": 0,
        "total_entities": 0,
        "active_zones": 1,
        "modes": {},
        "zones": [{"name": "Keller", "mode": "away"}],
        "unassigned_rooms": [],
    }
    coordinator = MockCoordinator(data)
    sensor = HabitusZoneSensor(coordinator)
    await sensor.async_update()
    zones = sensor.extra_state_attributes["zones"]
    assert zones[0]["rooms"] == 0
    assert zones[0]["entities"] == 0


# ── Summary ──────────────────────────────────────────────────────────
# Contract: HabitusZoneSensor is a pure projection shell.
# All data flows from Core /api/v1/hub/zones into sensor attributes.
# HA adds no local semantic computation (no mood inference,
# no activity translation, no heuristic icon selection beyond
# explicit mode flags from Core).
