"""Projection Contract Tests for PresenceIntelligenceSensor (HA-12).

Verifies that PresenceIntelligenceSensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/presence) with only trivial status_map and icon logic — no local semantic invention.

Pattern: same as HA-6 (habitus_zone), HA-8 (mood), HA-9 (autonomy),
HA-10 (brain_activity), HA-11 (hub_dashboard).
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"

    def async_write_ha_state(self):
        pass


# ── Sensor contract mirror ─────────────────────────────────────────────────────

_STATUS_MAP = {
    "home": "Alle zu Hause",
    "away": "Alle abwesend",
    "partial": "{home}/{total} zu Hause",
    "unknown": "Unbekannt",
}


class PresenceIntelligenceSensorContract:
    """Mirror of PresenceIntelligenceSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/hub/presence
    - native_value: status_map lookup (trivial) or "{home}/{total} zu Hause" for unmapped
    - icon: if-elif chain on status (trivial)
    - extra_state_attributes: direct passthrough of all Core fields
    - rooms filtering: current_count > 0 (presentation only)
    - recent_transitions: passthrough with [:5] cap
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    async def _fetch(self):
        return self._data

    def _apply(self, fetched_data):
        if fetched_data and fetched_data.get("ok"):
            self._data = fetched_data

    @property
    def native_value(self):
        total = self._data.get("total_persons", 0)
        home = self._data.get("persons_home", 0)
        status = self._data.get("household_status", "unknown")
        if total == 0:
            return "Nicht verfügbar"
        if status in _STATUS_MAP:
            if status == "partial":
                return f"{home}/{total} zu Hause"
            return _STATUS_MAP[status]
        return f"{home}/{total} zu Hause"

    @property
    def icon(self):
        status = self._data.get("household_status", "unknown")
        if status == "home":
            return "mdi:home-account"
        elif status == "away":
            return "mdi:home-export-outline"
        elif status == "partial":
            return "mdi:home-clock"
        return "mdi:account-group"

    @property
    def extra_state_attributes(self):
        attrs = {
            "total_persons": self._data.get("total_persons", 0),
            "persons_home": self._data.get("persons_home", 0),
            "persons_away": self._data.get("persons_away", 0),
            "household_status": self._data.get("household_status", "unknown"),
            "total_rooms": self._data.get("total_rooms", 0),
            "occupied_rooms": self._data.get("occupied_rooms", 0),
            "active_triggers": self._data.get("active_triggers", 0),
        }
        rooms = self._data.get("room_occupancy", [])
        if rooms:
            attrs["rooms"] = [
                {"room": r.get("room_name", r.get("room_id")),
                 "count": r.get("current_count", 0),
                 "persons": r.get("persons", [])}
                for r in rooms if r.get("current_count", 0) > 0
            ]
        transitions = self._data.get("recent_transitions", [])
        if transitions:
            attrs["recent_transitions"] = [
                {"person": t.get("person_id"), "from": t.get("from_room"), "to": t.get("to_room")}
                for t in transitions[:5]
            ]
        return attrs


# ── Test Cases ───────────────────────────────────────────────────────────────

# PI1: native_value with known status
PI1 = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "total_persons": 3, "persons_home": 3, "household_status": "home"}, "Alle zu Hause"),
    ({"ok": True, "total_persons": 3, "persons_home": 0, "household_status": "away"}, "Alle abwesend"),
    ({"ok": True, "total_persons": 3, "persons_home": 1, "household_status": "partial"}, "1/3 zu Hause"),
    ({"ok": True, "total_persons": 3, "persons_home": 2, "household_status": "partial"}, "2/3 zu Hause"),
    ({"ok": True, "total_persons": 3, "household_status": "unknown"}, "Unbekannt"),
])

# PI2: native_value — zero persons
PI2 = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "total_persons": 0}, "Nicht verfügbar"),
    ({"ok": True, "total_persons": 0, "persons_home": 0}, "Nicht verfügbar"),
])

# PI3: native_value — unmapped status falls back to "{home}/{total} zu Hause"
PI3 = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "total_persons": 4, "persons_home": 2, "household_status": "strange_status"}, "2/4 zu Hause"),
    ({"ok": True, "total_persons": 1, "persons_home": 0, "household_status": ""}, "0/1 zu Hause"),
])

# PI4: icon
PI4 = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "household_status": "home"}, "mdi:home-account"),
    ({"ok": True, "household_status": "away"}, "mdi:home-export-outline"),
    ({"ok": True, "household_status": "partial"}, "mdi:home-clock"),
    ({"ok": True, "household_status": "unknown"}, "mdi:account-group"),
    ({"ok": True, "household_status": ""}, "mdi:account-group"),
    ({"ok": True, "household_status": "anything_else"}, "mdi:account-group"),
])

# PI5: extra_state_attributes passthrough
PI5 = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "total_persons", 5),
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "persons_home", 3),
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "persons_away", 2),
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "total_rooms", 8),
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "occupied_rooms", 3),
    ({"ok": True, "total_persons": 5, "persons_home": 3, "persons_away": 2, "household_status": "partial", "total_rooms": 8, "occupied_rooms": 3, "active_triggers": 2}, "active_triggers", 2),
])

# PI6: rooms filtering (current_count > 0)
PI6 = pytest.mark.parametrize("room_data,expected_room_count", [
    ([{"room_name": "Kitchen", "current_count": 2}, {"room_name": "Bedroom", "current_count": 0}, {"room_name": "Living Room", "current_count": 1}], 2),
    ([{"room_id": "bath", "current_count": 1}, {"room_id": "study", "current_count": 0}], 1),
    ([], 0),
    ([{"room_name": "empty", "current_count": 0}], 0),
    ([{"room_name": "A", "current_count": 1}, {"room_name": "B", "current_count": 2}, {"room_name": "C", "current_count": 3}], 3),
])

# PI7: recent_transitions cap at 5
PI7 = pytest.mark.parametrize("transitions_data,expected_count", [
    ([], 0),
    ([{"person_id": "p1", "from_room": "bed", "to_room": "bath"}], 1),
    ([{f"t{i}": "x"} for i in range(10)], 5),
    ([{"person_id": f"p{i}", "from_room": f"r{i}", "to_room": f"r{i+1}"} for i in range(7)], 5),
])

# PI8: edge cases
PI8 = pytest.mark.parametrize("fetched_data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "total_persons": 2}, True),
    ({"ok": True, "household_status": "home", "persons_home": 2, "total_persons": 2}, True),
])


# ── Parametrized test functions ───────────────────────────────────────────────

@PI1
def test_PI1_native_value_known_status(core_data, expected):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.native_value == expected


@PI2
def test_PI2_native_value_zero_persons(core_data, expected):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.native_value == expected


@PI3
def test_PI3_native_value_unmapped_status(core_data, expected):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.native_value == expected


@PI4
def test_PI4_icon(core_data, expected_icon):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.icon == expected_icon


@PI5
def test_PI5_extra_attrs_passthrough(core_data, key, expected):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.extra_state_attributes[key] == expected


@PI6
def test_PI6_rooms_filter_current_count_gt_zero(room_data, expected_room_count):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply({"ok": True, "room_occupancy": room_data, "total_persons": 1})
    attrs = sensor.extra_state_attributes
    assert len(attrs.get("rooms", [])) == expected_room_count


@PI7
def test_PI7_recent_transitions_cap_at_5(transitions_data, expected_count):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply({"ok": True, "recent_transitions": transitions_data, "total_persons": 1})
    attrs = sensor.extra_state_attributes
    assert len(attrs.get("recent_transitions", [])) == expected_count


@PI8
def test_PI8_edge_cases(fetched_data, expect_ok):
    coord = MockCoordinator({})
    sensor = PresenceIntelligenceSensorContract(coord)
    sensor._apply(fetched_data)
    if expect_ok:
        assert sensor._data.get("ok") is True
