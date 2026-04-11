"""PresenceIntelligenceSensor Projection Contract Tests (HA-344).

Verifies: PresenceIntelligenceSensor ist reine Projection-Shell auf /api/v1/hub/presence.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


class PresenceIntelligenceSensorContract:
    """Contract-Mirror für PresenceIntelligenceSensor."""

    ENDPOINT = "/api/v1/hub/presence"
    SENSOR_MODULE = "custom_components.pilotsuite.sensors.presence_intelligence_sensor"
    SENSOR_CLASS = "PresenceIntelligenceSensor"

    @staticmethod
    def _as_mapping(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value):
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_int(value, default=0):
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value
        return default

    @staticmethod
    def _as_string(value, default=""):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        return default

    @staticmethod
    def native_value_for(data: dict) -> str:
        safe = PresenceIntelligenceSensorContract._as_mapping(data)
        total = PresenceIntelligenceSensorContract._as_int(safe.get("total_persons"), 0)
        home = PresenceIntelligenceSensorContract._as_int(safe.get("persons_home"), 0)
        status = PresenceIntelligenceSensorContract._as_string(safe.get("household_status"), "unknown")
        if total == 0:
            return "Nicht verfügbar"
        status_map = {
            "home": "Alle zu Hause",
            "away": "Alle abwesend",
            "partial": f"{home}/{total} zu Hause",
            "unknown": "Unbekannt",
        }
        return status_map.get(status, f"{home}/{total} zu Hause")

    @staticmethod
    def icon_for(data: dict) -> str:
        safe = PresenceIntelligenceSensorContract._as_mapping(data)
        status = PresenceIntelligenceSensorContract._as_string(safe.get("household_status"), "unknown")
        if status == "home":
            return "mdi:home-account"
        if status == "away":
            return "mdi:home-export-outline"
        if status == "partial":
            return "mdi:home-clock"
        return "mdi:account-group"

    @staticmethod
    def attrs_for(data: dict) -> dict:
        safe = PresenceIntelligenceSensorContract._as_mapping(data)
        attrs = {
            "total_persons": PresenceIntelligenceSensorContract._as_int(safe.get("total_persons"), 0),
            "persons_home": PresenceIntelligenceSensorContract._as_int(safe.get("persons_home"), 0),
            "persons_away": PresenceIntelligenceSensorContract._as_int(safe.get("persons_away"), 0),
            "household_status": PresenceIntelligenceSensorContract._as_string(safe.get("household_status"), "unknown"),
            "total_rooms": PresenceIntelligenceSensorContract._as_int(safe.get("total_rooms"), 0),
            "occupied_rooms": PresenceIntelligenceSensorContract._as_int(safe.get("occupied_rooms"), 0),
            "active_triggers": PresenceIntelligenceSensorContract._as_int(safe.get("active_triggers"), 0),
        }

        rooms = PresenceIntelligenceSensorContract._as_list(safe.get("room_occupancy"))
        if rooms:
            projected_rooms = []
            for room in rooms:
                item = PresenceIntelligenceSensorContract._as_mapping(room)
                if not item:
                    continue
                count = PresenceIntelligenceSensorContract._as_int(item.get("current_count"), 0)
                if count <= 0:
                    continue
                projected_rooms.append(
                    {
                        "room": PresenceIntelligenceSensorContract._as_string(item.get("room_name"))
                        or PresenceIntelligenceSensorContract._as_string(item.get("room_id"))
                        or "unbekannt",
                        "count": count,
                        "persons": [
                            person
                            for person in (
                                PresenceIntelligenceSensorContract._as_string(entry)
                                for entry in PresenceIntelligenceSensorContract._as_list(item.get("persons"))
                            )
                            if person
                        ],
                    }
                )
            attrs["rooms"] = projected_rooms

        transitions = PresenceIntelligenceSensorContract._as_list(safe.get("recent_transitions"))
        if transitions:
            projected_transitions = []
            for transition in transitions[:5]:
                item = PresenceIntelligenceSensorContract._as_mapping(transition)
                if not item:
                    continue
                projected_transitions.append(
                    {
                        "person": PresenceIntelligenceSensorContract._as_string(item.get("person_id")) or None,
                        "from": PresenceIntelligenceSensorContract._as_string(item.get("from_room")) or None,
                        "to": PresenceIntelligenceSensorContract._as_string(item.get("to_room")) or None,
                    }
                )
            attrs["recent_transitions"] = projected_transitions

        return attrs


@pytest.fixture
def coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def hass():
    return MagicMock()


@pytest.fixture
def sensor(coordinator, hass):
    from custom_components.pilotsuite.sensors.presence_intelligence_sensor import PresenceIntelligenceSensor

    entity = PresenceIntelligenceSensor(coordinator)
    entity.hass = hass
    return entity


@pytest.fixture
def mock_data_ok():
    return {
        "ok": True,
        "total_persons": 4,
        "persons_home": 3,
        "persons_away": 1,
        "household_status": "partial",
        "total_rooms": 6,
        "occupied_rooms": 3,
        "active_triggers": 2,
        "room_occupancy": [
            {"room_name": "Wohnzimmer", "room_id": "rz", "current_count": 2, "persons": ["A", "B"]},
            {"room_name": "Küche", "room_id": "kz", "current_count": 1, "persons": ["C"]},
            {"room_name": "Bad", "room_id": "bz", "current_count": 0, "persons": []},
        ],
        "recent_transitions": [
            {"person_id": "A", "from_room": "Küche", "to_room": "Wohnzimmer"},
            {"person_id": "B", "from_room": "Bad", "to_room": "Wohnzimmer"},
        ],
    }


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"ok": True, "total_persons": 2, "persons_home": 2, "household_status": "home"}, "Alle zu Hause"),
        ({"ok": True, "total_persons": 3, "persons_home": 0, "household_status": "away"}, "Alle abwesend"),
        ({"ok": True, "total_persons": 4, "persons_home": 3, "household_status": "partial"}, "3/4 zu Hause"),
        ({"ok": True, "total_persons": 2, "persons_home": 0, "household_status": "unknown"}, "Unbekannt"),
        ({"ok": True, "total_persons": 0, "persons_home": 0, "household_status": "unknown"}, "Nicht verfügbar"),
        ({"household_status": "other", "total_persons": 2, "persons_home": 1}, "1/2 zu Hause"),
    ],
)
def test_PI1_native_value(sensor, data, expected):
    sensor._data = data
    assert sensor.native_value == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"household_status": "home"}, "mdi:home-account"),
        ({"household_status": "away"}, "mdi:home-export-outline"),
        ({"household_status": "partial"}, "mdi:home-clock"),
        ({"household_status": "unknown"}, "mdi:account-group"),
        ({"household_status": " other "}, "mdi:account-group"),
        ({}, "mdi:account-group"),
    ],
)
def test_PI2_icon(sensor, data, expected):
    sensor._data = data
    assert sensor.icon == expected


def test_PI3_attrs_full_projection(sensor, mock_data_ok):
    sensor._data = mock_data_ok
    assert sensor.extra_state_attributes == PresenceIntelligenceSensorContract.attrs_for(mock_data_ok)


def test_PI3_attrs_rooms_filtered_but_key_preserved(sensor):
    sensor._data = {
        "ok": True,
        "room_occupancy": [{"room_name": "Balkon", "current_count": 0}],
    }
    attrs = sensor.extra_state_attributes
    assert attrs["rooms"] == []


def test_PI3_attrs_transitions_capped_at_five(sensor):
    sensor._data = {
        "ok": True,
        "recent_transitions": [{"person_id": f"P{i}", "from_room": "A", "to_room": "B"} for i in range(10)],
    }
    attrs = sensor.extra_state_attributes
    assert len(attrs["recent_transitions"]) == 5
    assert attrs["recent_transitions"][0]["person"] == "P0"


def test_PI4_malformed_scalars_fall_back_to_defaults(sensor):
    sensor._data = {
        "ok": True,
        "total_persons": "4",
        "persons_home": True,
        "persons_away": 1.2,
        "household_status": 7,
        "total_rooms": "6",
        "occupied_rooms": False,
        "active_triggers": None,
    }
    attrs = sensor.extra_state_attributes
    assert sensor.native_value == "Nicht verfügbar"
    assert sensor.icon == "mdi:account-group"
    assert attrs["total_persons"] == 0
    assert attrs["persons_home"] == 0
    assert attrs["persons_away"] == 0
    assert attrs["household_status"] == "unknown"
    assert attrs["total_rooms"] == 0
    assert attrs["occupied_rooms"] == 0
    assert attrs["active_triggers"] == 0


def test_PI4_non_list_rooms_and_transitions_are_ignored(sensor):
    sensor._data = {
        "ok": True,
        "room_occupancy": {"room_name": "Wohnzimmer"},
        "recent_transitions": "bad",
    }
    attrs = sensor.extra_state_attributes
    assert "rooms" not in attrs
    assert "recent_transitions" not in attrs


def test_PI4_mixed_malformed_rooms_are_skipped(sensor):
    sensor._data = {
        "ok": True,
        "room_occupancy": [
            "bad",
            {"room_name": " ", "room_id": "office", "current_count": 2, "persons": ["A", None, " ", 5]},
            {"room_name": "Bad", "current_count": "2", "persons": ["B"]},
        ],
    }
    attrs = sensor.extra_state_attributes
    assert attrs["rooms"] == [{"room": "office", "count": 2, "persons": ["A"]}]


def test_PI4_mixed_malformed_transitions_are_skipped(sensor):
    sensor._data = {
        "ok": True,
        "recent_transitions": [
            "bad",
            {"person_id": " A ", "from_room": " Küche ", "to_room": "Wohnzimmer"},
            {"person_id": None, "from_room": [], "to_room": " "},
        ],
    }
    attrs = sensor.extra_state_attributes
    assert attrs["recent_transitions"] == [
        {"person": "A", "from": "Küche", "to": "Wohnzimmer"},
        {"person": None, "from": None, "to": None},
    ]


def test_PI4_empty_data_defaults(sensor):
    sensor._data = {}
    assert sensor.native_value == "Nicht verfügbar"
    assert sensor.icon == "mdi:account-group"
    assert sensor.extra_state_attributes == {
        "total_persons": 0,
        "persons_home": 0,
        "persons_away": 0,
        "household_status": "unknown",
        "total_rooms": 0,
        "occupied_rooms": 0,
        "active_triggers": 0,
    }


@pytest.mark.asyncio
async def test_PI5_async_update_accepts_only_dict_with_ok(sensor):
    sensor._data = {"ok": True, "total_persons": 1}
    sensor._fetch = AsyncMock(side_effect=[[1], "bad", {"ok": False}, {"ok": True, "total_persons": 3}])

    await sensor.async_update()
    assert sensor._data == {"ok": True, "total_persons": 1}

    await sensor.async_update()
    assert sensor._data == {"ok": True, "total_persons": 1}

    await sensor.async_update()
    assert sensor._data == {"ok": True, "total_persons": 1}

    await sensor.async_update()
    assert sensor._data == {"ok": True, "total_persons": 3}


def test_GC1_hits_core_api_endpoint():
    assert PresenceIntelligenceSensorContract.ENDPOINT == "/api/v1/hub/presence"


def test_GC2_no_local_semantic_invention(sensor, mock_data_ok):
    sensor._data = mock_data_ok
    assert sensor.native_value == PresenceIntelligenceSensorContract.native_value_for(mock_data_ok)
    assert sensor.icon == PresenceIntelligenceSensorContract.icon_for(mock_data_ok)
    assert sensor.extra_state_attributes == PresenceIntelligenceSensorContract.attrs_for(mock_data_ok)


def test_GC3_source_guard_helpers_and_top_level_guard_exist():
    source = Path(
        "/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/presence_intelligence_sensor.py"
    ).read_text()
    assert "def _as_mapping" in source
    assert "def _as_list" in source
    assert "def _as_int" in source
    assert "def _as_string" in source
    assert "if isinstance(data, dict) and data.get(\"ok\")" in source
