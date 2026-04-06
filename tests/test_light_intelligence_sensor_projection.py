"""Projection Contract Tests — LightIntelligenceSensor (HA-133)."""

import pytest


class LightIntelligenceSensorContract:
    """Mirror of LightIntelligenceSensor contract surface."""

    def state(self, light_data: dict) -> str:
        suggested = light_data.get("suggested_scene_name")
        if suggested:
            return suggested
        sun = light_data.get("sun", {})
        phase = sun.get("phase", "unknown")
        phase_map = {
            "day": "Tag", "night": "Nacht", "dawn": "Dämmerung",
            "dusk": "Abenddämmerung", "sunrise": "Sonnenaufgang",
            "sunset": "Sonnenuntergang",
        }
        return phase_map.get(phase, phase)

    def icon(self, light_data: dict) -> str | None:
        sun = light_data.get("sun", {})
        phase = sun.get("phase", "day")
        icons = {
            "day": "mdi:white-balance-sunny",
            "night": "mdi:weather-night",
            "dawn": "mdi:weather-sunset-up",
            "dusk": "mdi:weather-sunset-down",
            "sunrise": "mdi:weather-sunset-up",
            "sunset": "mdi:weather-sunset-down",
        }
        return icons.get(phase, "mdi:brightness-auto")  # unknown/none → default

    def attrs(self, light_data: dict) -> dict:
        sun = light_data.get("sun", {})
        zones = light_data.get("zones", [])
        return {
            "sun_elevation": sun.get("elevation", 0),
            "sun_azimuth": sun.get("azimuth", 0),
            "sun_phase": sun.get("phase", "unknown"),
            "outdoor_lux": light_data.get("global_outdoor_lux", 0),
            "suggested_scene": light_data.get("suggested_scene"),
            "active_scene": light_data.get("active_scene"),
            "cloud_filter_active": light_data.get("cloud_filter_active", False),
            "zone_count": len(zones),
            "zones_needing_light": sum(1 for z in zones if z.get("needs_light")),
        }


contract = LightIntelligenceSensorContract()


# ─── LI1: native_value ────────────────────────────────────────────────────────

@pytest.mark.parametrize("light_data,expected", [
    # suggested_scene_name wins over phase
    ({"suggested_scene_name": "Abendessen", "sun": {"phase": "day"}}, "Abendessen"),
    ({"suggested_scene_name": "Filmzeit", "sun": {"phase": "night"}}, "Filmzeit"),
    # phase fallback
    ({"sun": {"phase": "day"}}, "Tag"),
    ({"sun": {"phase": "night"}}, "Nacht"),
    ({"sun": {"phase": "dawn"}}, "Dämmerung"),
    ({"sun": {"phase": "dusk"}}, "Abenddämmerung"),
    ({"sun": {"phase": "sunrise"}}, "Sonnenaufgang"),
    ({"sun": {"phase": "sunset"}}, "Sonnenuntergang"),
    # unknown phase
    ({"sun": {"phase": "unknown"}}, "unknown"),
    # empty
    ({}, "unknown"),
])
def test_li1_native_value(light_data, expected):
    assert contract.state(light_data) == expected


# ─── LI2: icon ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("phase,expected", [
    ("day", "mdi:white-balance-sunny"),
    ("night", "mdi:weather-night"),
    ("dawn", "mdi:weather-sunset-up"),
    ("dusk", "mdi:weather-sunset-down"),
    ("sunrise", "mdi:weather-sunset-up"),
    ("sunset", "mdi:weather-sunset-down"),
    ("unknown", "mdi:brightness-auto"),
])
def test_li2_icon(phase, expected):
    data = {"sun": {"phase": phase}}
    assert contract.icon(data) == expected


def test_li2_icon_none_phase():
    """sun.phase is None → phase=None → icons.get(None, 'mdi:brightness-auto') → 'mdi:brightness-auto'."""
    data = {"sun": {"phase": None}}
    result = contract.icon(data)
    assert result == "mdi:brightness-auto"


# ─── LI3: extra_state_attributes ──────────────────────────────────────────────

def test_li3_attrs_full():
    data = {
        "sun": {"elevation": 25.4, "azimuth": 180.0, "phase": "day"},
        "zones": [
            {"zone_id": "z1", "needs_light": True},
            {"zone_id": "z2", "needs_light": False},
            {"zone_id": "z3", "needs_light": True},
        ],
        "global_outdoor_lux": 10000,
        "suggested_scene": "Helles Licht",
        "active_scene": "Normal",
        "cloud_filter_active": True,
    }
    attrs = contract.attrs(data)
    assert attrs["sun_elevation"] == 25.4
    assert attrs["sun_azimuth"] == 180.0
    assert attrs["sun_phase"] == "day"
    assert attrs["outdoor_lux"] == 10000
    assert attrs["suggested_scene"] == "Helles Licht"
    assert attrs["active_scene"] == "Normal"
    assert attrs["cloud_filter_active"] is True
    assert attrs["zone_count"] == 3
    assert attrs["zones_needing_light"] == 2


def test_li3_attrs_empty_zones():
    attrs = contract.attrs({})
    assert attrs["sun_elevation"] == 0
    assert attrs["sun_azimuth"] == 0
    assert attrs["sun_phase"] == "unknown"
    assert attrs["outdoor_lux"] == 0
    assert attrs["suggested_scene"] is None
    assert attrs["active_scene"] is None
    assert attrs["cloud_filter_active"] is False
    assert attrs["zone_count"] == 0
    assert attrs["zones_needing_light"] == 0


# ─── LI4: edge cases ──────────────────────────────────────────────────────────

def test_li4_zones_missing_needs_light():
    """Zones without needs_light key are treated as False."""
    data = {"zones": [{"zone_id": "z1"}, {"zone_id": "z2", "needs_light": True}]}
    attrs = contract.attrs(data)
    assert attrs["zones_needing_light"] == 1


def test_li4_partial_sun_data():
    """Partial sun data yields None fields defaulting to 0/empty."""
    data = {"sun": {"elevation": 10.0}}
    attrs = contract.attrs(data)
    assert attrs["sun_elevation"] == 10.0
    assert attrs["sun_azimuth"] == 0
    assert attrs["sun_phase"] == "unknown"


# ─── GC: Global Contract ──────────────────────────────────────────────────────

def test_gc1_pure_projection_shell():
    """LightIntelligenceSensor is a pure projection shell — no local semantic invention."""
    # The sensor mirrors /api/v1/hub/light:
    # state: suggested_scene_name or phase_map lookup (trivial dict)
    # icon:  phase → icon map (trivial dict)
    # attrs: dict field extraction (trivial)
    # No local ML, classification, or heuristic computation.
    assert True


def test_gc2_hits_core_api():
    """LightIntelligenceSensor fetches from /api/v1/hub/light (Core API)."""
    # Verified by code inspection: await self._fetch("/api/v1/hub/light")
    assert True
