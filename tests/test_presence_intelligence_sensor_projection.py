"""Projection Contract Tests for PresenceIntelligenceSensor.

Verifies: Pure Projection Shell on /api/v1/hub/presence — no local semantics.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# Contract Mirrors
# =============================================================================
class PresenceIntelligenceSensorContract:
    """Mirror of the sensor's projection contract."""
    # native_value: simple dict lookup + status_map (trivial, no semantics)
    # icon: simple if-elif-else on status (trivial, no semantics)
    # extra_state_attributes: straight pass-through of API fields
    ENDPOINT = "/api/v1/hub/presence"
    SOURCE = "coordinator.data (via _fetch() → Core API)"


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def sensor():
    """Build a PresenceIntelligenceSensor with mocked coordinator."""
    from custom_components.pilotsuite.sensors.presence_intelligence_sensor import (
        PresenceIntelligenceSensor,
    )
    coordinator = MagicMock()
    coordinator.hass = MagicMock()
    sensor = PresenceIntelligenceSensor(coordinator)
    return sensor


@pytest.fixture
def mock_data_ok():
    """Full valid presence data."""
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


@pytest.fixture
def mock_data_home():
    """All persons home."""
    return {
        "ok": True,
        "total_persons": 2,
        "persons_home": 2,
        "persons_away": 0,
        "household_status": "home",
        "total_rooms": 3,
        "occupied_rooms": 2,
        "active_triggers": 0,
        "room_occupancy": [],
        "recent_transitions": [],
    }


@pytest.fixture
def mock_data_away():
    """All persons away."""
    return {
        "ok": True,
        "total_persons": 3,
        "persons_home": 0,
        "persons_away": 3,
        "household_status": "away",
        "total_rooms": 4,
        "occupied_rooms": 0,
        "active_triggers": 1,
        "room_occupancy": [],
        "recent_transitions": [],
    }


@pytest.fixture
def mock_data_unknown():
    """Unknown status."""
    return {
        "ok": True,
        "total_persons": 2,
        "persons_home": 0,
        "persons_away": 0,
        "household_status": "unknown",
        "total_rooms": 2,
        "occupied_rooms": 0,
        "active_triggers": 0,
        "room_occupancy": [],
        "recent_transitions": [],
    }


@pytest.fixture
def mock_data_zero_persons():
    """total_persons = 0."""
    return {
        "ok": True,
        "total_persons": 0,
        "persons_home": 0,
        "persons_away": 0,
        "household_status": "unknown",
        "total_rooms": 0,
        "occupied_rooms": 0,
        "active_triggers": 0,
        "room_occupancy": [],
        "recent_transitions": [],
    }


@pytest.fixture
def mock_data_no_ok():
    """API response without ok=True."""
    return {"total_persons": 1}


@pytest.fixture
def mock_data_missing_fields():
    """Partial data, missing optional fields."""
    return {"ok": True, "total_persons": 1, "persons_home": 1}


@pytest.fixture
def mock_data_rooms_only():
    """Only room_occupancy data, no transitions."""
    return {
        "ok": True,
        "total_persons": 5,
        "persons_home": 5,
        "persons_away": 0,
        "household_status": "home",
        "total_rooms": 3,
        "occupied_rooms": 1,
        "active_triggers": 0,
        "room_occupancy": [
            {"room_name": "Schlafzimmer", "current_count": 2, "persons": ["X", "Y"]},
        ],
        "recent_transitions": [],
    }


# =============================================================================
# PI1: native_value — status_map trivial lookup
# =============================================================================
class TestPINativeValue:
    """PI1: native_value via status_map (trivial dict lookup)."""

    @pytest.mark.parametrize("data_fixture,expected", [
        ("mock_data_home", "Alle zu Hause"),
        ("mock_data_away", "Alle abwesend"),
        ("mock_data_ok", "3/4 zu Hause"),
        ("mock_data_unknown", "Unbekannt"),
        ("mock_data_zero_persons", "Nicht verfügbar"),
    ])
    def test_pi1_native_value_by_status(self, sensor, request, data_fixture, expected):
        mock_data = request.getfixturevalue(data_fixture)
        sensor._data = mock_data
        assert sensor.native_value == expected

    def test_pi1_unknown_fallback(self, sensor, mock_data_unknown):
        sensor._data = mock_data_unknown
        assert sensor.native_value == "Unbekannt"


# =============================================================================
# PI2: icon — if-elif-else on status (trivial)
# =============================================================================
class TestPIIcon:
    """PI2: icon via if-elif-else (trivial)."""

    @pytest.mark.parametrize("status,expected_icon", [
        ("home", "mdi:home-account"),
        ("away", "mdi:home-export-outline"),
        ("partial", "mdi:home-clock"),
        ("unknown", "mdi:account-group"),
    ])
    def test_pi2_icon_by_status(self, sensor, status, expected_icon):
        sensor._data = {"household_status": status}
        assert sensor.icon == expected_icon


# =============================================================================
# PI3: extra_state_attributes — straight pass-through
# =============================================================================
class TestPIAttrs:
    """PI3: extra_state_attributes — direct API field pass-through."""

    def test_pi3_attrs_full(self, sensor, mock_data_ok):
        sensor._data = mock_data_ok
        attrs = sensor.extra_state_attributes
        assert attrs["total_persons"] == 4
        assert attrs["persons_home"] == 3
        assert attrs["persons_away"] == 1
        assert attrs["household_status"] == "partial"
        assert attrs["total_rooms"] == 6
        assert attrs["occupied_rooms"] == 3
        assert attrs["active_triggers"] == 2

    def test_pi3_attrs_rooms_filtered(self, sensor, mock_data_ok):
        """Rooms with current_count=0 are filtered out."""
        sensor._data = mock_data_ok
        attrs = sensor.extra_state_attributes
        rooms = attrs["rooms"]
        assert len(rooms) == 2
        assert rooms[0]["room"] == "Wohnzimmer"
        assert rooms[0]["count"] == 2
        assert rooms[1]["room"] == "Küche"
        assert rooms[1]["count"] == 1

    def test_pi3_attrs_transitions_capped(self, sensor, mock_data_ok):
        """Only last 5 transitions included."""
        sensor._data = mock_data_ok
        attrs = sensor.extra_state_attributes
        transitions = attrs["recent_transitions"]
        assert len(transitions) == 2
        assert transitions[0]["person"] == "A"
        assert transitions[0]["from"] == "Küche"
        assert transitions[0]["to"] == "Wohnzimmer"

    def test_pi3_attrs_empty(self, sensor, mock_data_home):
        sensor._data = mock_data_home
        attrs = sensor.extra_state_attributes
        # mock_data_home has room_occupancy=[] → "rooms" key not added
        assert "rooms" not in attrs
        assert "recent_transitions" not in attrs

    def test_pi3_attrs_missing_fields(self, sensor, mock_data_missing_fields):
        """Missing optional fields default to 0."""
        sensor._data = mock_data_missing_fields
        attrs = sensor.extra_state_attributes
        assert attrs["total_rooms"] == 0
        assert attrs["occupied_rooms"] == 0
        assert attrs["active_triggers"] == 0


# =============================================================================
# PI4: Edge cases
# =============================================================================
class TestPIEdge:
    """PI4: edge cases."""

    def test_pi4_empty_data(self, sensor):
        """No data at all."""
        sensor._data = {}
        assert sensor.native_value == "Nicht verfügbar"
        assert sensor.icon == "mdi:account-group"

    def test_pi4_no_ok_flag(self, sensor, mock_data_no_ok):
        """API returns without ok=True; sensor still processes data."""
        sensor._data = mock_data_no_ok
        # mock_data_no_ok has status="unknown" → status_map["unknown"]="Unbekannt"
        assert sensor.native_value == "Unbekannt"

    def test_pi4_unknown_status_fallback(self, sensor):
        """Unknown status not in map → fallback f-string."""
        sensor._data = {"household_status": "other", "total_persons": 2, "persons_home": 1}
        assert sensor.native_value == "1/2 zu Hause"

    def test_pi4_room_missing_fields(self, sensor):
        """Room entry with current_count=0 is filtered out."""
        sensor._data = {
            "ok": True,
            "total_persons": 1,
            "persons_home": 1,
            "household_status": "home",
            "total_rooms": 1,
            "occupied_rooms": 1,
            "active_triggers": 0,
            "room_occupancy": [{"room_name": "Balkon", "current_count": 0}],
            "recent_transitions": [],
        }
        attrs = sensor.extra_state_attributes
        # current_count=0 → filtered out → rooms=[]
        assert attrs["rooms"] == []

    def test_pi4_transition_missing_person(self, sensor):
        """Transition entry with missing optional fields."""
        sensor._data = {
            "ok": True,
            "total_persons": 1,
            "persons_home": 1,
            "household_status": "home",
            "total_rooms": 1,
            "occupied_rooms": 1,
            "active_triggers": 0,
            "room_occupancy": [],
            "recent_transitions": [{"from_room": "Küche", "to_room": "Wohnzimmer"}],
        }
        attrs = sensor.extra_state_attributes
        assert attrs["recent_transitions"][0]["person"] is None
        assert attrs["recent_transitions"][0]["from"] == "Küche"


# =============================================================================
# GC: Global Contract
# =============================================================================
class TestPIGlobalContract:
    """GC1–GC2: global contract — pure projection, no local semantic invention."""

    def test_gc1_hits_core_api_endpoint(self, sensor):
        """GC1: source is /api/v1/hub/presence."""
        assert PresenceIntelligenceSensorContract.ENDPOINT == "/api/v1/hub/presence"
        assert PresenceIntelligenceSensorContract.SOURCE.startswith("coordinator.data")

    def test_gc2_no_local_semantic_invention(self, sensor, mock_data_ok):
        """GC2: all values are direct API pass-through; status_map is trivial lookup."""
        sensor._data = mock_data_ok
        # native_value: pure dict lookup + status_map (no classification logic)
        nv = sensor.native_value
        assert isinstance(nv, str)
        # icon: pure if-elif (no ML, no heuristic)
        ic = sensor.icon
        assert ic.startswith("mdi:")
        # attrs: direct field extraction (no computation)
        attrs = sensor.extra_state_attributes
        assert attrs["total_persons"] == mock_data_ok["total_persons"]
        assert attrs["persons_home"] == mock_data_ok["persons_home"]
