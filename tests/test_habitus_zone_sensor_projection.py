"""Projection contract tests for habitus_zone_sensor.py (v6.5.0).

Consumes GET /api/v1/habitus/zones from Core.
Contract: {status, total_zones, zones: [{id, zone_type, name_de, name_en,
         description, priority, icon, module_overrides, metrics?}]}
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_coordinator():
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator._config = {}
    coordinator.async_get_clientsession = AsyncMock(return_value=MagicMock())
    return coordinator


def _make_sensor():
    from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
    coordinator = _make_coordinator()
    sensor = HabitusZoneSensor(coordinator)
    return sensor


# ─────────────────────────────────────────────────────────────────────────────
# Core /api/v1/habitus/zones contract fixtures
# ─────────────────────────────────────────────────────────────────────────────

_HABITUS_ZONES_PAYLOAD = {
    "status": "ok",
    "total_zones": 10,
    "zones": [
        {
            "id": "living",
            "zone_type": "living",
            "name_de": "Wohnbereich",
            "name_en": "Living Area",
            "description": " Wohn- und Essbereich",
            "keywords_de": ["wohn", "wohnzimmer", "esszimmer"],
            "keywords_en": ["living", "lounge", "dining"],
            "priority": 10,
            "icon": "mdi:sofa",
            "module_overrides": {"light": True, "motion": True, "music": True, "volume": True, "tv": True, "climate": True},
            "metrics": {"presence_count": 2, "light_level": 75, "temperature": 22.1},
        },
        {
            "id": "bath",
            "zone_type": "bath",
            "name_de": "Badbereich",
            "name_en": "Bath Area",
            "description": "Badezimmer und Sanitärbereich",
            "keywords_de": ["bad", "badezimmer", "dusche"],
            "keywords_en": ["bath", "bathroom", "shower"],
            "priority": 7,
            "icon": "mdi:shower",
            "module_overrides": {"light": True, "motion": True, "climate": True},
        },
        {
            "id": "bedroom",
            "zone_type": "bedroom",
            "name_de": "Schlafbereich",
            "name_en": "Bedroom",
            "description": "Schlafzimmer",
            "keywords_de": ["schlaf", "schlafzimmer"],
            "keywords_en": ["bedroom", "sleep"],
            "priority": 5,
            "icon": "mdi:bed",
            "module_overrides": {"light": True, "motion": True, "climate": True},
            "active": False,
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# HC native_value / state contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHZState:
    """HC state contract for HabitusZoneSensor."""

    def test_hz1_no_data_returns_keine_zonen(self):
        """When no zone data, state shows 'Keine Zonen'."""
        sensor = _make_sensor()
        sensor._zone_data = {}
        assert sensor.state == "Keine Zonen"

    def test_hz2_total_zones_zero(self):
        """When total_zones=0, state shows 'Keine Zonen'."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 0, "zones": []}
        assert sensor.state == "Keine Zonen"

    def test_hz3_counts_active_and_total(self):
        """State formats as '{active}/{total} aktiv' using explicit active flags."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 3,
            "zones": [
                {"id": "z1", "active": True, "priority": 10},
                {"id": "z2", "active": False, "priority": 5},
                {"id": "z3", "active": True, "priority": 3},
            ],
        }
        assert sensor.state == "2/3 aktiv"

    def test_hz4_infers_active_from_priority_when_no_explicit_flag(self):
        """When no explicit active flag, zones with priority > 0 count as active."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 2,
            "zones": [
                {"id": "z1", "priority": 10},   # priority > 0 → active
                {"id": "z2", "priority": 0},    # priority = 0 → not active
            ],
        }
        assert sensor.state == "1/2 aktiv"

    def test_hz5_explicit_active_takes_precedence(self):
        """Explicit active=False wins over priority > 0."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 1,
            "zones": [
                {"id": "z1", "active": False, "priority": 10},
            ],
        }
        assert sensor.state == "0/1 aktiv"


# ─────────────────────────────────────────────────────────────────────────────
# HC icon contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHZIcon:
    """HC icon contract — icon derived from zone_type of first zone."""

    def test_hz6_icon_default_no_zones(self):
        """When no zone data, default icon is home-floor-1."""
        sensor = _make_sensor()
        sensor._zone_data = {}
        assert sensor.icon == "mdi:home-floor-1"

    def test_hz7_icon_from_zone_type_living(self):
        """zone_type='living' → mdi:sofa."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 1, "zones": [{"id": "living", "zone_type": "living"}]}
        assert sensor.icon == "mdi:sofa"

    def test_hz8_icon_from_zone_type_bath(self):
        """zone_type='bath' → mdi:shower."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 1, "zones": [{"id": "bath", "zone_type": "bath"}]}
        assert sensor.icon == "mdi:shower"

    def test_hz9_icon_from_zone_type_bedroom(self):
        """zone_type='bedroom' → mdi:bed."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 1, "zones": [{"id": "bedroom", "zone_type": "bedroom"}]}
        assert sensor.icon == "mdi:bed"

    def test_hz10_icon_from_zone_type_office(self):
        """zone_type='office' → mdi:desk."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 1, "zones": [{"id": "office", "zone_type": "office"}]}
        assert sensor.icon == "mdi:desk"

    def test_hz11_icon_unknown_type_falls_back(self):
        """Unknown zone_type falls back to default."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 1, "zones": [{"id": "unknown", "zone_type": "unknown"}]}
        assert sensor.icon == "mdi:home-floor-1"


# ─────────────────────────────────────────────────────────────────────────────
# HC extra_state_attributes contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHZAttrs:
    """HC extra_state_attributes contract for HabitusZoneSensor."""

    def test_hz12_attrs_full_payload(self):
        """Full Core habitus/zones payload maps correctly into attributes."""
        sensor = _make_sensor()
        sensor._zone_data = _HABITUS_ZONES_PAYLOAD
        attrs = sensor.extra_state_attributes

        assert attrs["total_zones"] == 10
        zones = attrs["zones"]
        assert len(zones) == 3

        # First zone — full data
        z0 = zones[0]
        assert z0["id"] == "living"
        assert z0["zone_type"] == "living"
        assert z0["name"] == "Wohnbereich"
        assert z0["name_de"] == "Wohnbereich"
        assert z0["name_en"] == "Living Area"
        assert z0["priority"] == 10
        assert z0["icon"] == "mdi:sofa"
        assert z0["module_overrides"] == {"light": True, "motion": True, "music": True, "volume": True, "tv": True, "climate": True}
        assert z0["metrics"] == {"presence_count": 2, "light_level": 75, "temperature": 22.1}

        # Second zone — no metrics
        z1 = zones[1]
        assert z1["id"] == "bath"
        assert z1["zone_type"] == "bath"
        assert "metrics" not in z1

    def test_hz13_attrs_minimal_zone(self):
        """Zone with only id and zone_type maps without errors."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 1,
            "zones": [{"id": "corridor", "zone_type": "corridor"}],
        }
        attrs = sensor.extra_state_attributes
        z = attrs["zones"][0]
        assert z["id"] == "corridor"
        assert z["zone_type"] == "corridor"
        assert z["name"] == ""
        assert z["priority"] == 0
        assert z["module_overrides"] == {}

    def test_hz14_attrs_empty_zones(self):
        """Empty zones list returns empty zones attr."""
        sensor = _make_sensor()
        sensor._zone_data = {"total_zones": 0, "zones": []}
        attrs = sensor.extra_state_attributes
        assert attrs["total_zones"] == 0
        assert attrs["zones"] == []

    def test_hz15_attrs_no_metrics_key_when_absent(self):
        """metrics key is omitted from zone entry when not in payload."""
        sensor = _make_sensor()
        sensor._zone_data = {
            "total_zones": 1,
            "zones": [{"id": "outdoor", "zone_type": "outdoor", "priority": 2}],
        }
        attrs = sensor.extra_state_attributes
        assert "metrics" not in attrs["zones"][0]


# ─────────────────────────────────────────────────────────────────────────────
# async_update contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHZUpdate:
    """async_update fetches from the canonical Core endpoint."""

    def test_hz16_fetch_url_is_habitus_zones(self):
        """async_update calls _fetch with /api/v1/habitus/zones."""
        import inspect
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        source = inspect.getsource(HabitusZoneSensor.async_update)
        assert "/api/v1/habitus/zones" in source

    def test_hz17_fetch_includes_metrics_param(self):
        """async_update requests include_metrics=true."""
        import inspect
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        source = inspect.getsource(HabitusZoneSensor.async_update)
        assert "include_metrics=true" in source


# ─────────────────────────────────────────────────────────────────────────────
# Global projection contract
# ─────────────────────────────────────────────────────────────────────────────

class TestHZGlobalContract:
    """Global projection contract for HabitusZoneSensor."""

    def test_gc1_no_hub_zones_url(self):
        """Sensor no longer references the non-existent /api/v1/hub/zones."""
        import inspect
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        source = inspect.getsource(HabitusZoneSensor)
        assert "/api/v1/hub/zones" not in source

    def test_gc2_uses_canonical_habitus_zones_endpoint(self):
        """Sensor uses the canonical /api/v1/habitus/zones endpoint."""
        import inspect
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        source = inspect.getsource(HabitusZoneSensor.async_update)
        assert "/api/v1/habitus/zones" in source

    def test_gc3_zone_list_derives_from_zone_data(self):
        """Zones list comes from _zone_data['zones'], not local inference."""
        sensor = _make_sensor()
        sensor._zone_data = _HABITUS_ZONES_PAYLOAD
        attrs = sensor.extra_state_attributes
        assert len(attrs["zones"]) == 3
        assert attrs["zones"][0]["id"] == "living"
        assert attrs["zones"][2]["id"] == "bedroom"

    def test_gc4_inherits_from_copilot_base_entity(self):
        """HabitusZoneSensor inherits from CopilotBaseEntity for auth/API."""
        from custom_components.pilotsuite.sensors.habitus_zone_sensor import HabitusZoneSensor
        from custom_components.pilotsuite.entity import CopilotBaseEntity
        assert issubclass(HabitusZoneSensor, CopilotBaseEntity)
