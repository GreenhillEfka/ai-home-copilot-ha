"""Projection Contract Tests for RegionalContextSensor (HA-130).

Verifies RegionalContextSensor is a pure projection shell on /api/v1/regional/context.
Cases: RC1 native_value + RC2 extra_state_attributes + RC3 solar fields +
RC4 grid_price_eur_kwh + RC5 edge + GC1-GC2 global.
"""
import pytest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.pilotsuite.sensors.regional_context_sensor import (
    RegionalContextSensor,
)


def make_sensor(data=None):
    """Create RegionalContextSensor with a MagicMock coordinator and optional data."""
    coordinator = MagicMock()
    coordinator._core_base_url.return_value = "http://localhost:8012"
    coordinator._core_headers.return_value = {"Authorization": "Bearer test"}
    sensor = RegionalContextSensor(coordinator)
    sensor._data = data if data is not None else {}
    return sensor


# ─── RC1: native_value ────────────────────────────────────────────────────────

class TestRCNativeValue:
    """native_value returns '{country_code} — {region}' from location dict."""

    @pytest.mark.parametrize("country,region,expected", [
        ("DE", "Berlin", "DE — Berlin"),
        ("AT", "Wien", "AT — Wien"),
        ("CH", "Zürich", "CH — Zürich"),
        ("??", "Unknown", "?? — Unknown"),
    ])
    def test_rc1_location_string(self, country, region, expected):
        data = {
            "ok": True,
            "location": {"country_code": country, "region": region},
        }
        s = make_sensor(data)
        assert s.native_value == expected

    def test_rc1_missing_location(self):
        s = make_sensor({})
        assert s.native_value == "?? — Unknown"

    def test_rc1_missing_country(self):
        data = {"location": {"region": "Berlin"}}
        s = make_sensor(data)
        assert s.native_value == "?? — Berlin"

    def test_rc1_missing_region(self):
        data = {"location": {"country_code": "DE"}}
        s = make_sensor(data)
        assert s.native_value == "DE — Unknown"

    def test_rc1_empty_data(self):
        s = make_sensor(None)
        s._data = {}
        assert s.native_value == "?? — Unknown"


# ─── RC2: extra_state_attributes — location ───────────────────────────────────

class TestRCLocationAttrs:
    """extra_state_attributes expose location fields verbatim from API."""

    def test_rc2_full_location(self):
        data = {
            "ok": True,
            "location": {
                "latitude": 52.52,
                "longitude": 13.405,
                "country_code": "DE",
                "region": "Berlin",
                "timezone": "Europe/Berlin",
            },
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["latitude"] == 52.52
        assert attrs["longitude"] == 13.405
        assert attrs["country"] == "DE"
        assert attrs["region"] == "Berlin"
        assert attrs["timezone"] == "Europe/Berlin"

    def test_rc2_location_missing_optional(self):
        data = {"location": {"country_code": "DE", "region": "Berlin"}}
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["latitude"] is None
        assert attrs["longitude"] is None
        assert attrs["timezone"] is None


# ─── RC3: extra_state_attributes — solar ──────────────────────────────────────

class TestRCSolarAttrs:
    """extra_state_attributes expose solar fields verbatim from API."""

    def test_rc3_full_solar(self):
        data = {
            "location": {},
            "solar": {
                "sunrise": "06:12",
                "sunset": "20:15",
                "day_length_hours": 14.05,
                "elevation_deg": 45.2,
                "is_daylight": True,
            },
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["sunrise"] == "06:12"
        assert attrs["sunset"] == "20:15"
        assert attrs["day_length_hours"] == 14.05
        assert attrs["solar_elevation_deg"] == 45.2
        assert attrs["is_daylight"] is True

    def test_rc3_solar_missing_optional(self):
        data = {"location": {}, "solar": {}}
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["sunrise"] is None
        assert attrs["sunset"] is None
        assert attrs["day_length_hours"] is None
        assert attrs["solar_elevation_deg"] is None
        assert attrs["is_daylight"] is None

    def test_rc3_is_daylight_false(self):
        data = {"solar": {"is_daylight": False}}
        s = make_sensor(data)
        assert s.extra_state_attributes["is_daylight"] is False


# ─── RC4: extra_state_attributes — defaults (grid_price / feed_in / weather / language) ─

class TestRCDefaultAttrs:
    """extra_state_attributes expose defaults (tariff, weather config, language)."""

    def test_rc4_full_defaults(self):
        data = {
            "defaults": {
                "grid_price_eur_kwh": 0.28,
                "feed_in_tariff_eur_kwh": 0.082,
                "weather_service": "DWD",
                "language": "de",
            },
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["grid_price_eur_kwh"] == 0.28
        assert attrs["feed_in_tariff_eur_kwh"] == 0.082
        assert attrs["weather_service"] == "DWD"
        assert attrs["language"] == "de"

    def test_rc4_defaults_missing(self):
        data = {}
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["grid_price_eur_kwh"] is None
        assert attrs["feed_in_tariff_eur_kwh"] is None
        assert attrs["weather_service"] is None
        assert attrs["language"] is None


# ─── RC5: edge cases ───────────────────────────────────────────────────────────

class TestRCEdge:
    """Edge cases: empty _data, missing location key, location_synced flag."""

    def test_rc5_empty_data(self):
        s = make_sensor(None)
        s._data = {}
        attrs = s.extra_state_attributes
        assert attrs["latitude"] is None
        assert attrs["sunrise"] is None
        assert attrs["grid_price_eur_kwh"] is None

    def test_rc5_no_location_key(self):
        data = {"solar": {"sunrise": "07:00"}}
        s = make_sensor(data)
        assert s.native_value == "?? — Unknown"
        assert s.extra_state_attributes["sunrise"] == "07:00"

    def test_rc5_no_solar_key(self):
        data = {"location": {"country_code": "AT", "region": "Wien"}}
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["sunrise"] is None
        assert attrs["is_daylight"] is None

    def test_rc5_location_synced_false_by_default(self):
        s = make_sensor({})
        assert s.extra_state_attributes["location_synced"] is False


# ─── GC1-GC2: global contract ───────────────────────────────────────────────

class TestRCGlobalContract:
    """Global contract: pure projection on /api/v1/regional, no local semantic invention."""

    def test_gc1_icon(self):
        # _attr_icon is a class attribute, not an instance property
        assert RegionalContextSensor._attr_icon == "mdi:map-marker-radius"

    def test_gc2_no_local_semantic_invention(self):
        # All values are verbatim API lookups — no threshold, no classification
        data = {
            "location": {"country_code": "DE", "region": "Berlin"},
            "solar": {"is_daylight": True, "elevation_deg": 55.0},
            "defaults": {"grid_price_eur_kwh": 0.30},
        }
        s = make_sensor(data)
        # native_value: pure dict lookup
        assert s.native_value == "DE — Berlin"
        # solar fields: verbatim
        assert s.extra_state_attributes["is_daylight"] is True
        assert s.extra_state_attributes["solar_elevation_deg"] == 55.0
        # defaults: verbatim
        assert s.extra_state_attributes["grid_price_eur_kwh"] == 0.30
