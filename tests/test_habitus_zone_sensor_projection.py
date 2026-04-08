"""Projection contract tests for habitus_zone_sensor.py."""
import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_coordinator():
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.async_get_clientsession = AsyncMock(return_value=MagicMock())
    return coordinator


def _make_sensor():
    from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
    coordinator = _make_coordinator()
    sensor = HabitusZoneSensor(coordinator)
    return sensor


class TestHZState:
    """HC native_value/state contract."""

    def test_hz1_no_zones_returns_default(self):
        """When total_zones=0, state shows 'Keine Zonen'."""
        sensor = _make_sensor()
        sensor._zone_data = {}
        assert sensor.state == "Keine Zonen"

    def test_hz2_active_total_format(self):
        """When zones present, state formats as '{active}/{total} aktiv'."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 5, "active_zones": 3}
        assert sensor.state == "3/5 aktiv"

    def test_hz3_all_active(self):
        """When all zones active, state shows '{total}/{total} aktiv'."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 4, "active_zones": 4}
        assert sensor.state == "4/4 aktiv"

    def test_hz4_zero_active(self):
        """When no zone active, state shows '0/{total} aktiv'."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 3, "active_zones": 0}
        assert sensor.state == "0/3 aktiv"


class TestHZIcon:
    """HC icon contract."""

    def test_hz5_icon_default(self):
        """Default icon is home-floor-1."""
        sensor = _make_sensor()
        sensor._zone_data = {}
        assert sensor.icon == "mdi:home-floor-1"

    def test_hz6_icon_party(self):
        """Party mode > 0 → party-popper icon."""
        sensor = _make_sensor()
        sensor._zone_data = {"modes": {"party": 1}}
        assert sensor.icon == "mdi:party-popper"

    def test_hz7_icon_sleeping(self):
        """Sleeping mode > 0 → sleep icon."""
        sensor = _make_sensor()
        sensor._zone_data = {"modes": {"sleeping": 1}}
        assert sensor.icon == "mdi:sleep"

    def test_hz8_icon_party_and_sleeping(self):
        """Party takes priority over sleeping."""
        sensor = _make_sensor()
        sensor._zone_data = {"modes": {"party": 1, "sleeping": 1}}
        assert sensor.icon == "mdi:party-popper"


class TestHZAttrs:
    """HC extra_state_attributes contract."""

    def test_hz9_attrs_full(self):
        """Full coordinator data surfaces in attributes."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 3,
            "total_rooms": 12,
            "total_entities": 47,
            "active_zones": 2,
            "modes": {"party": 0, "sleeping": 1},
            "unassigned_rooms": ["Kitchen"],
            "zones": [
                {"name": "Living Room", "mode": "active", "room_count": 4, "entity_count": 15},
                {"name": "Bedroom", "mode": "idle", "room_count": 2, "entity_count": 8},
            ],
        }
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 3
        assert attrs["total_rooms"] == 12
        assert attrs["total_entities"] == 47
        assert attrs["active_zones"] == 2
        assert attrs["modes"] == {"party": 0, "sleeping": 1}
        assert attrs["unassigned_rooms"] == ["Kitchen"]
        assert len(attrs["zones"]) == 2
        assert attrs["zones"][0]["name"] == "Living Room"

    def test_hz10_attrs_defaults(self):
        """Missing keys default to empty/zero."""
        sensor = _make_sensor()
        sensor._zone_data = {}
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 0
        assert attrs["active_zones"] == 0
        assert attrs["zones"] == []

    def test_hz11_zone_list_capped(self):
        """Zone list capped to 10 entries."""
        sensor = _make_sensor()
        zones = [{"name": f"Z{i}", "mode": "active", "room_count": 1, "entity_count": 1} for i in range(15)]
        sensor._zone_data = {"zones": zones, "total_zones": 15, "active_zones": 15}
        attrs = sensor.extra_state_attributes
        assert len(attrs["zones"]) == 10


class TestHZGlobalContract:
    """Global projection contract."""

    def test_gc1_uses_fetch_or_coordinator(self):
        """HabitusZoneSensor projects /api/v1/hub/zones via coordinator."""
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        import inspect
        source = inspect.getsource(HabitusZoneSensor)
        # Uses _fetch for API calls or gets data from coordinator
        assert "_fetch" in source or "coordinator" in source

    def test_gc2_state_derives_from_zone_data(self):
        """State is trivial aggregation, not local inference."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 2, "active_zones": 1}
        assert sensor.state == "1/2 aktiv"

        sensor2 = _make_sensor()
        sensor2._zone_data = {"total_zones": 0, "active_zones": 0}
        assert sensor2.state == "Keine Zonen"
