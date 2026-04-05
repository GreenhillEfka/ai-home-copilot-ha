"""Projection Contract Tests for LightIntelligenceSensor (HA-20a) and WeatherOptimizerSensor (HA-20b).

Both are pure Projection-Shells on Core-truth with trivial presentation logic only.
Pattern: same as HA-6 through HA-19.
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


# ── LightIntelligenceSensor contract ───────────────────────────────────────────────

_PHASE_MAP = {
    "day": "Tag", "night": "Nacht", "dawn": "Dämmerung",
    "dusk": "Abenddämmerung", "sunrise": "Sonnenaufgang",
    "sunset": "Sonnenuntergang",
}
_PHASE_ICONS = {
    "day": "mdi:white-balance-sunny", "night": "mdi:weather-night",
    "dawn": "mdi:weather-sunset-up", "dusk": "mdi:weather-sunset-down",
    "sunrise": "mdi:weather-sunset-up", "sunset": "mdi:weather-sunset-down",
}


class LightIntelligenceSensorContract:
    """Mirror of LightIntelligenceSensor projection logic.

    Contract:
    - _fetch(): hits /api/v1/hub/light
    - state: suggested_scene_name | phase_map[phase] | phase (fallback)
    - icon: _PHASE_ICONS lookup
    - extra_state_attributes: passthrough of sun/zones data
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._light_data = {}

    def apply(self, data):
        if data:
            self._light_data = data

    @property
    def state(self):
        suggested = self._light_data.get("suggested_scene_name")
        if suggested:
            return suggested
        sun = self._light_data.get("sun", {})
        phase = sun.get("phase", "unknown")
        return _PHASE_MAP.get(phase, phase)

    @property
    def icon(self):
        sun = self._light_data.get("sun", {})
        phase = sun.get("phase", "unknown")
        return _PHASE_ICONS.get(phase, "mdi:brightness-auto")

    @property
    def extra_state_attributes(self):
        sun = self._light_data.get("sun", {})
        zones = self._light_data.get("zones", [])
        return {
            "sun_elevation": sun.get("elevation", 0),
            "sun_azimuth": sun.get("azimuth", 0),
            "sun_phase": sun.get("phase", "unknown"),
            "outdoor_lux": self._light_data.get("global_outdoor_lux", 0),
            "suggested_scene": self._light_data.get("suggested_scene"),
            "active_scene": self._light_data.get("active_scene"),
            "cloud_filter_active": self._light_data.get("cloud_filter_active", False),
            "zone_count": len(zones),
            "zones_needing_light": sum(1 for z in zones if z.get("needs_light")),
        }


# ── WeatherOptimizerSensor contract ─────────────────────────────────────────────

class WeatherOptimizerSensorContract:
    """Mirror of WeatherOptimizerSensor projection logic.

    Contract:
    - hits /api/v1/predict/weather-optimize
    - native_value: int (score)
    - extra_state_attributes: passthrough
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        return self._data.get("score")

    @property
    def extra_state_attributes(self):
        return {
            "score": self._data.get("score"),
            "recommended_action": self._data.get("recommended_action"),
            "confidence": self._data.get("confidence"),
            "weather_condition": self._data.get("weather_condition"),
        }


# ── LightIntelligenceSensor test cases ─────────────────────────────────────────

LI1 = pytest.mark.parametrize("data,expected", [
    ({"suggested_scene_name": "Abendroutine"}, "Abendroutine"),
    ({"sun": {"phase": "day"}}, "Tag"),
    ({"sun": {"phase": "night"}}, "Nacht"),
    ({"sun": {"phase": "dawn"}}, "Dämmerung"),
    ({"sun": {"phase": "dusk"}}, "Abenddämmerung"),
    ({"sun": {"phase": "sunrise"}}, "Sonnenaufgang"),
    ({"sun": {"phase": "sunset"}}, "Sonnenuntergang"),
    ({"sun": {"phase": "unknown_phase"}}, "unknown_phase"),
    ({}, "unknown"),
    ({"sun": {}}, "unknown"),
])
LI2 = pytest.mark.parametrize("data,expected_icon", [
    ({"sun": {"phase": "day"}}, "mdi:white-balance-sunny"),
    ({"sun": {"phase": "night"}}, "mdi:weather-night"),
    ({"sun": {"phase": "dawn"}}, "mdi:weather-sunset-up"),
    ({"sun": {"phase": "dusk"}}, "mdi:weather-sunset-down"),
    ({"sun": {"phase": "sunrise"}}, "mdi:weather-sunset-up"),
    ({"sun": {"phase": "sunset"}}, "mdi:weather-sunset-down"),
    ({}, "mdi:brightness-auto"),
    ({"sun": {}}, "mdi:brightness-auto"),
])
LI3 = pytest.mark.parametrize("data,key,expected", [
    ({"sun": {"elevation": 45.0, "azimuth": 180.0, "phase": "day"}}, "sun_elevation", 45.0),
    ({"sun": {"elevation": 45.0, "azimuth": 180.0, "phase": "day"}}, "sun_azimuth", 180.0),
    ({"global_outdoor_lux": 50000, "cloud_filter_active": True, "zones": [{"needs_light": True}, {"needs_light": False}]}, "outdoor_lux", 50000),
    ({"global_outdoor_lux": 50000, "cloud_filter_active": True, "zones": [{"needs_light": True}, {"needs_light": False}]}, "cloud_filter_active", True),
    ({"global_outdoor_lux": 50000, "cloud_filter_active": True, "zones": [{"needs_light": True}, {"needs_light": False}]}, "zone_count", 2),
    ({"global_outdoor_lux": 50000, "cloud_filter_active": True, "zones": [{"needs_light": True}, {"needs_light": False}]}, "zones_needing_light", 1),
])
LI4 = pytest.mark.parametrize("data,expected_count", [
    ([{"needs_light": True}, {"needs_light": False}], 1),
    ([{"needs_light": True}, {"needs_light": True}], 2),
    ([], 0),
])


# ── WeatherOptimizerSensor test cases ─────────────────────────────────────────

WO1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "score": 85}, 85),
    ({"ok": True, "score": 0}, 0),
    ({"ok": True, "score": 100}, 100),
    ({"ok": True, "score": None}, None),
    ({}, None),
])
WO2 = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "score": 85, "recommended_action": "open_windows", "confidence": 0.92, "weather_condition": "sunny"}, "recommended_action", "open_windows"),
    ({"ok": True, "score": 85, "recommended_action": "open_windows", "confidence": 0.92, "weather_condition": "sunny"}, "confidence", 0.92),
    ({"ok": True, "score": 85, "recommended_action": "open_windows", "confidence": 0.92, "weather_condition": "sunny"}, "weather_condition", "sunny"),
])


@LI1
def test_LI1_state(data, expected):
    s = LightIntelligenceSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.state == expected


@LI2
def test_LI2_icon(data, expected_icon):
    s = LightIntelligenceSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.icon == expected_icon


@LI3
def test_LI3_attrs(data, key, expected):
    s = LightIntelligenceSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected


@LI4
def test_LI4_zones_needing_light(data, expected_count):
    s = LightIntelligenceSensorContract(MockCoordinator({}))
    s.apply({"zones": data})
    assert s.extra_state_attributes["zones_needing_light"] == expected_count


@WO1
def test_WO1_native_value(data, expected):
    s = WeatherOptimizerSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@WO2
def test_WO2_attrs(data, key, expected):
    s = WeatherOptimizerSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected
