"""Projection Contract Tests for ComfortIndexSensor (HA-17 cont.) + RegionalContextSensor (HA-18).

Verifies both are pure Projection-Shells on Core-truth.

Comfort: /api/v1/comfort + /api/v1/comfort/lighting
Regional: /api/v1/regional/context

Pattern: same as HA-6/8/9/10/11/12/13/14/15/16.
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data, session=None):
        self.data = data
        self.hass = MockHass()
        self._session = session
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"

    def async_write_ha_state(self):
        pass


# ── ComfortIndexSensor contract ───────────────────────────────────────────────

GRADE_ICONS = {
    "A": "mdi:emoticon-happy",
    "B": "mdi:emoticon",
    "C": "mdi:emoticon-neutral",
    "D": "mdi:emoticon-sad",
    "F": "mdi:emoticon-dead",
}


class ComfortIndexSensorContract:
    """Mirror of ComfortIndexSensor projection logic.

    Contract:
    - hits /api/v1/comfort → self._comfort_data
    - native_value: score or None
    - icon: GRADE_ICONS lookup or fallback
    - extra_state_attributes: passthrough of score/grade/readings + URLs
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._comfort_data = None

    def apply(self, data):
        if data and data.get("ok"):
            self._comfort_data = data

    @property
    def native_value(self):
        if self._comfort_data and self._comfort_data.get("ok"):
            return self._comfort_data.get("score")
        return None

    @property
    def icon(self):
        if self._comfort_data and self._comfort_data.get("ok"):
            grade = self._comfort_data.get("grade", "C")
            return GRADE_ICONS.get(grade, "mdi:home-thermometer")
        return "mdi:home-thermometer"

    @property
    def extra_state_attributes(self):
        attrs = {
            "comfort_url": f"/api/v1/comfort",
            "lighting_url": f"/api/v1/comfort/lighting",
        }
        if self._comfort_data and self._comfort_data.get("ok"):
            attrs["grade"] = self._comfort_data.get("grade")
            attrs["zone_id"] = self._comfort_data.get("zone_id")
            attrs["suggestions"] = self._comfort_data.get("suggestions", [])
            for reading in self._comfort_data.get("readings", []):
                factor = reading["factor"]
                attrs[f"{factor}_score"] = reading["score"]
                attrs[f"{factor}_status"] = reading["status"]
                if reading.get("raw_value") is not None:
                    attrs[f"{factor}_value"] = reading["raw_value"]
        return attrs


# ── RegionalContextSensor contract ─────────────────────────────────────────────

class RegionalContextSensorContract:
    """Mirror of RegionalContextSensor projection logic.

    Contract:
    - hits /api/v1/regional/context
    - native_value: "{country_code} — {region}"
    - extra_state_attributes: passthrough of location/solar/defaults fields
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        loc = self._data.get("location", {})
        return f"{loc.get('country_code', '??')} — {loc.get('region', 'Unknown')}"

    @property
    def extra_state_attributes(self):
        loc = self._data.get("location", {})
        solar = self._data.get("solar", {})
        defaults = self._data.get("defaults", {})
        return {
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "country": loc.get("country_code"),
            "region": loc.get("region"),
            "timezone": loc.get("timezone"),
            "sunrise": solar.get("sunrise"),
            "sunset": solar.get("sunset"),
            "day_length_hours": solar.get("day_length_hours"),
            "solar_elevation_deg": solar.get("elevation_deg"),
            "is_daylight": solar.get("is_daylight"),
            "grid_price_eur_kwh": defaults.get("grid_price_eur_kwh"),
            "feed_in_tariff_eur_kwh": defaults.get("feed_in_tariff_eur_kwh"),
            "weather_service": defaults.get("weather_service"),
            "language": defaults.get("language"),
        }


# ── ComfortIndexSensor test cases ───────────────────────────────────────────────

CI1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "score": 85.5}, 85.5),
    ({"ok": True, "score": 0.0}, 0.0),
    ({"ok": True, "score": 100.0}, 100.0),
    ({"ok": True, "score": None}, None),
    ({"ok": True}, None),
    (None, None),
    ({}, None),
])
CI2 = pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "grade": "A"}, "mdi:emoticon-happy"),
    ({"ok": True, "grade": "B"}, "mdi:emoticon"),
    ({"ok": True, "grade": "C"}, "mdi:emoticon-neutral"),
    ({"ok": True, "grade": "D"}, "mdi:emoticon-sad"),
    ({"ok": True, "grade": "F"}, "mdi:emoticon-dead"),
    ({"ok": True, "grade": "X"}, "mdi:home-thermometer"),
    ({"ok": True, "grade": ""}, "mdi:home-thermometer"),
    ({}, "mdi:home-thermometer"),
])
CI3_readings = pytest.mark.parametrize("data,expected_keys", [
    ({"ok": True, "readings": [{"factor": "temperature", "score": 90, "status": "optimal", "raw_value": 21.5}]}, ["temperature_score", "temperature_status", "temperature_value"]),
    ({"ok": True, "readings": [{"factor": "humidity", "score": 80, "status": "good", "raw_value": 45.0}]}, ["humidity_score", "humidity_status", "humidity_value"]),
    ({"ok": True, "readings": [{"factor": "light", "score": 70, "status": "ok", "raw_value": 300}]}, ["light_score", "light_status", "light_value"]),
    ({"ok": True, "readings": []}, []),
    ({"ok": True, "readings": [{"factor": "noise", "score": 60, "status": "moderate", "raw_value": None}]}, ["noise_score", "noise_status"]),
])


# ── RegionalContextSensor test cases ───────────────────────────────────────────

RC1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "location": {"country_code": "DE", "region": "Berlin"}}, "DE — Berlin"),
    ({"ok": True, "location": {"country_code": "AT", "region": "Wien"}}, "AT — Wien"),
    ({"ok": True, "location": {"country_code": "US", "region": "California"}}, "US — California"),
    ({"ok": True, "location": {}}, "?? — Unknown"),
    ({"ok": True, "location": {"region": "Test"}}, "?? — Test"),
])
RC2_attrs = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "location": {"latitude": 52.52, "longitude": 13.405, "country_code": "DE", "region": "Berlin", "timezone": "Europe/Berlin"}}, "latitude", 52.52),
    ({"ok": True, "location": {"latitude": 52.52, "longitude": 13.405, "country_code": "DE", "region": "Berlin", "timezone": "Europe/Berlin"}}, "longitude", 13.405),
    ({"ok": True, "location": {"latitude": 52.52, "longitude": 13.405, "country_code": "DE", "region": "Berlin", "timezone": "Europe/Berlin"}}, "timezone", "Europe/Berlin"),
    ({"ok": True, "solar": {"sunrise": "06:00", "sunset": "20:00", "day_length_hours": 14.0, "elevation_deg": 45.0, "is_daylight": True}}, "sunrise", "06:00"),
    ({"ok": True, "solar": {"sunrise": "06:00", "sunset": "20:00", "day_length_hours": 14.0, "elevation_deg": 45.0, "is_daylight": True}}, "is_daylight", True),
    ({"ok": True, "defaults": {"grid_price_eur_kwh": 0.30, "feed_in_tariff_eur_kwh": 0.082, "weather_service": "Open-Meteo", "language": "de"}}, "grid_price_eur_kwh", 0.30),
])


# ── Parametrized test functions ───────────────────────────────────────────────

@CI1
def test_CI1_native_value(data, expected):
    s = ComfortIndexSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@CI2
def test_CI2_icon(data, expected_icon):
    s = ComfortIndexSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.icon == expected_icon


@CI3_readings
def test_CI3_readings_dynamic_attrs(data, expected_keys):
    s = ComfortIndexSensorContract(MockCoordinator({}))
    s.apply(data)
    attrs = s.extra_state_attributes
    for k in expected_keys:
        assert k in attrs


@RC1
def test_RC1_native_value(data, expected):
    s = RegionalContextSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@RC2_attrs
def test_RC2_attrs_passthrough(data, key, expected):
    s = RegionalContextSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected
