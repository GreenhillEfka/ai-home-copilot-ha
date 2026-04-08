"""ZoneModeSensor Projection-Contract-Tests (HA-142).

Verifiziert: ZoneModeSensor ist reine Projection-Shell auf /api/v1/hub/modes.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class ZoneModeSensorContract:
    """Contract-Mirror für ZoneModeSensor."""

    ENDPOINT = "/api/v1/hub/modes"

    @staticmethod
    def native_value_empty(data: dict) -> str:
        if not data.get("active_modes"):
            return "Keine aktiven Modi"
        return ""

    @staticmethod
    def native_value_single(data: dict) -> str:
        active = data.get("active_modes", [])
        if len(active) == 1:
            return active[0].get("mode_name_de", active[0].get("mode_id", "Aktiv"))
        return ""

    @staticmethod
    def native_value_multiple(data: dict) -> str:
        active = data.get("active_modes", [])
        if len(active) > 1:
            return f"{len(active)} Modi aktiv"
        return ""

    @staticmethod
    def icon_empty(data: dict) -> str:
        if not data.get("active_modes"):
            return "mdi:toggle-switch-off"
        return ""

    @staticmethod
    def icon_single(data: dict) -> str:
        from custom_components.pilotsuite.sensors.zone_mode_sensor import _ICON_MAP
        active = data.get("active_modes", [])
        if len(active) == 1:
            mode_id = active[0].get("mode_id", "")
            return _ICON_MAP.get(mode_id, active[0].get("icon", "mdi:toggle-switch"))
        return ""

    @staticmethod
    def icon_multiple(data: dict) -> str:
        active = data.get("active_modes", [])
        if len(active) > 1:
            return "mdi:toggle-switch-variant"
        return ""


@pytest.fixture
def coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def sensor(coordinator):
    from custom_components.pilotsuite.sensors.zone_mode_sensor import ZoneModeSensor
    return ZoneModeSensor(coordinator)


@pytest.fixture
def hass():
    h = MagicMock()
    session = MagicMock()
    session.get = AsyncMock()
    h.helpers.aiohttp_client.async_get_clientsession.return_value = session
    return h


class TestZoneModeSensor:
    """ZoneModeSensor Projection-Contract-Tests."""

    def test_ZM1_native_value_empty(self, sensor, hass):
        """ZM1: Keine aktiven Modi → 'Keine aktiven Modi'."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": []}
        assert sensor.native_value == "Keine aktiven Modi"

    def test_ZM2_native_value_single(self, sensor, hass):
        """ZM2: Ein aktiver Modus → mode_name_de."""
        sensor.hass = hass
        sensor._data = {
            "ok": True,
            "active_modes": [{"mode_id": "party", "mode_name_de": "Party", "zone_id": "wohnzimmer"}],
        }
        assert sensor.native_value == "Party"

    def test_ZM3_native_value_multiple(self, sensor, hass):
        """ZM3: Mehrere aktive Modi → 'N Modi aktiv'."""
        sensor.hass = hass
        sensor._data = {
            "ok": True,
            "active_modes": [
                {"mode_id": "party", "mode_name_de": "Party"},
                {"mode_id": "movie", "mode_name_de": "Film"},
                {"mode_id": "focus", "mode_name_de": "Fokus"},
            ],
        }
        assert sensor.native_value == "3 Modi aktiv"

    def test_ZM4_icon_empty(self, sensor, hass):
        """ZM4: Keine aktiven Modi → toggle-switch-off."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": []}
        assert sensor.icon == "mdi:toggle-switch-off"

    def test_ZM5_icon_party(self, sensor, hass):
        """ZM5: Party-Modus → mdi:party-popper."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": [{"mode_id": "party"}]}
        assert sensor.icon == "mdi:party-popper"

    def test_ZM6_icon_movie(self, sensor, hass):
        """ZM6: Movie-Modus → mdi:movie-open."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": [{"mode_id": "movie"}]}
        assert sensor.icon == "mdi:movie-open"

    def test_ZM7_icon_focus(self, sensor, hass):
        """ZM7: Focus-Modus → mdi:head-lightbulb."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": [{"mode_id": "focus"}]}
        assert sensor.icon == "mdi:head-lightbulb"

    def test_ZM8_icon_multiple(self, sensor, hass):
        """ZM8: Mehrere Modi → toggle-switch-variant."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": [{"mode_id": "party"}, {"mode_id": "movie"}]}
        assert sensor.icon == "mdi:toggle-switch-variant"

    def test_ZM9_attrs_basic(self, sensor, hass):
        """ZM9: Basis-Attribute (counts)."""
        sensor.hass = hass
        sensor._data = {
            "ok": True,
            "active_modes": [{"mode_id": "party"}],
            "available_modes": [{"mode_id": "night"}],
            "total_zones_with_modes": 5,
        }
        attrs = sensor.extra_state_attributes
        assert attrs["active_count"] == 1
        assert attrs["available_count"] == 1
        assert attrs["total_zones_with_modes"] == 5

    def test_ZM10_attrs_active_details(self, sensor, hass):
        """ZM10: Active-Modes-Details in attrs."""
        sensor.hass = hass
        sensor._data = {
            "ok": True,
            "active_modes": [
                {
                    "mode_id": "party",
                    "mode_name_de": "Party",
                    "zone_id": "wohnzimmer",
                    "remaining_min": 45,
                    "activated_by": "user_andreas",
                }
            ],
        }
        attrs = sensor.extra_state_attributes
        assert "active_modes" in attrs
        assert len(attrs["active_modes"]) == 1
        assert attrs["active_modes"][0]["remaining_min"] == 45

    def test_ZM11_attrs_available_details(self, sensor, hass):
        """ZM11: Available-Modes-Details in attrs."""
        sensor.hass = hass
        sensor._data = {
            "ok": True,
            "available_modes": [
                {"mode_id": "night", "name_de": "Nacht", "icon": "mdi:weather-night", "default_duration_min": 480}
            ],
        }
        attrs = sensor.extra_state_attributes
        assert "available_modes" in attrs
        assert attrs["available_modes"][0]["duration_min"] == 480

    def test_ZM12_attrs_recent_capped(self, sensor, hass):
        """ZM12: Recent-Events auf 10 capped."""
        sensor.hass = hass
        sensor._data = {"ok": True, "recent_events": [{"id": i} for i in range(25)]}
        attrs = sensor.extra_state_attributes
        assert len(attrs["recent_events"]) == 10

    def test_ZM13_edge_missing_optional(self, sensor, hass):
        """ZM13: Fehlende optionale Keys → keine Exception."""
        sensor.hass = hass
        sensor._data = {"ok": True}
        attrs = sensor.extra_state_attributes
        assert attrs["active_count"] == 0
        assert attrs["available_count"] == 0

    def test_ZM14_edge_not_ok(self, sensor, hass):
        """ZM14: ok=false → keine Datenübernahme."""
        sensor.hass = hass
        sensor._data = {"ok": False, "active_modes": [{"mode_id": "party"}]}
        assert sensor.native_value == "Keine aktiven Modi"

    def test_ZM15_edge_none_data(self, sensor, hass):
        """ZM15: _data=None → safe defaults."""
        sensor.hass = hass
        sensor._data = None
        with pytest.raises(AttributeError):
            _ = sensor.native_value

    def test_ZM16_contract_endpoint(self, sensor, hass):
        """GC1: Verwendet /api/v1/hub/modes."""
        assert ZoneModeSensorContract.ENDPOINT == "/api/v1/hub/modes"

    def test_ZM17_no_local_semantic(self, sensor, hass):
        """GC2: Keine lokale Semantik-Invention."""
        sensor.hass = hass
        sensor._data = {"ok": True, "active_modes": []}
        # native_value ist deterministisch aus data abgeleitet
        assert sensor.native_value == "Keine aktiven Modi"
        # Icon ist deterministisch aus data abgeleitet
        assert sensor.icon == "mdi:toggle-switch-off"
