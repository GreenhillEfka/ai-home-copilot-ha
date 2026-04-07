"""Projection Contract Tests for ComfortIndexSensor (HA-129).

Verifies ComfortIndexSensor is a pure projection shell on /api/v1/comfort.
Cases: CI1 native_value + CI2 icon + CI3 attrs + CI4 edge + GC1-GC2 global.
"""
import pytest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from custom_components.copilot_ha.sensors.comfort_index_sensor import (
    ComfortIndexSensor,
    GRADE_ICONS,
)


def make_sensor(data=None):
    """Create ComfortIndexSensor with a MagicMock coordinator and optional data."""
    coordinator = MagicMock()
    coordinator._core_base_url.return_value = "http://localhost:8012"
    coordinator._core_headers.return_value = {"Authorization": "Bearer test"}
    sensor = ComfortIndexSensor(coordinator)
    # Attach coordinator so _core_base_url() works in attrs
    sensor.coordinator = coordinator
    if data is not None:
        sensor._comfort_data = data
    return sensor


# ─── CI1: native_value ────────────────────────────────────────────────────────

class TestCINativeValue:
    """native_value returns comfort score float when ok=True, else None."""

    @pytest.mark.parametrize("score,expected", [
        (85.0, 85.0),
        (0.0, 0.0),
        (100.0, 100.0),
        (42.7, 42.7),
    ])
    def test_ci1_ok_score(self, score, expected):
        data = {"ok": True, "score": score, "grade": "B"}
        s = make_sensor(data)
        assert s.native_value == expected

    def test_ci1_ok_missing_score(self):
        data = {"ok": True}
        s = make_sensor(data)
        assert s.native_value is None

    def test_ci1_not_ok(self):
        data = {"ok": False, "score": 90.0}
        s = make_sensor(data)
        assert s.native_value is None

    def test_ci1_none(self):
        s = make_sensor(None)
        s._comfort_data = None
        assert s.native_value is None


# ─── CI2: icon ───────────────────────────────────────────────────────────────

class TestCIIcon:
    """icon is derived from comfort grade (A-F), default when no data."""

    @pytest.mark.parametrize("grade,expected_icon", [
        ("A", "mdi:emoticon-happy"),
        ("B", "mdi:emoticon"),
        ("C", "mdi:emoticon-neutral"),
        ("D", "mdi:emoticon-sad"),
        ("F", "mdi:emoticon-dead"),
    ])
    def test_ci2_grade_icon(self, grade, expected_icon):
        data = {"ok": True, "score": 75.0, "grade": grade}
        s = make_sensor(data)
        assert s.icon == expected_icon

    def test_ci2_unknown_grade(self):
        data = {"ok": True, "score": 50.0, "grade": "X"}
        s = make_sensor(data)
        assert s.icon == "mdi:home-thermometer"

    def test_ci2_default_icon_no_data(self):
        s = make_sensor(None)
        s._comfort_data = None
        assert s.icon == "mdi:home-thermometer"

    def test_ci2_not_ok(self):
        data = {"ok": False, "grade": "A"}
        s = make_sensor(data)
        assert s.icon == "mdi:home-thermometer"


# ─── CI3: extra_state_attributes ─────────────────────────────────────────────

class TestCIAttributes:
    """extra_state_attributes are pure dict lookups / derivations from API data."""

    def test_ci3_full_attrs(self):
        data = {
            "ok": True,
            "score": 82.0,
            "grade": "A",
            "zone_id": "living-room-1",
            "suggestions": ["Dim living room lights", "Close blinds"],
            "readings": [
                {"factor": "temperature", "score": 90, "status": "optimal", "raw_value": 21.5},
                {"factor": "humidity", "score": 85, "status": "optimal", "raw_value": 55.0},
                {"factor": "light", "score": 70, "status": "acceptable", "raw_value": 300.0},
            ],
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes

        assert attrs["grade"] == "A"
        assert attrs["zone_id"] == "living-room-1"
        assert attrs["suggestions"] == ["Dim living room lights", "Close blinds"]
        assert attrs["temperature_score"] == 90
        assert attrs["temperature_status"] == "optimal"
        assert attrs["temperature_value"] == 21.5
        assert attrs["humidity_score"] == 85
        assert attrs["light_score"] == 70
        assert attrs["light_status"] == "acceptable"
        assert attrs["light_value"] == 300.0
        assert "comfort_url" in attrs
        assert "lighting_url" in attrs

    def test_ci3_minimal_attrs(self):
        data = {"ok": True, "score": 50.0}
        s = make_sensor(data)
        attrs = s.extra_state_attributes

        assert "grade" not in attrs
        assert "suggestions" not in attrs
        assert "comfort_url" in attrs
        assert "lighting_url" in attrs

    def test_ci3_attrs_mirror_api_only(self):
        # Score/grade come straight from API — no local computation
        data = {"ok": True, "score": 99.9, "grade": "A", "zone_id": "test-zone"}
        s = make_sensor(data)
        assert s.native_value == 99.9
        assert s.icon == "mdi:emoticon-happy"
        assert s.extra_state_attributes["grade"] == "A"


# ─── CI4: edge cases ─────────────────────────────────────────────────────────

class TestCIEdge:
    """Edge cases: missing optional fields, empty suggestions, None readings."""

    def test_ci4_empty_suggestions(self):
        data = {"ok": True, "score": 60.0, "grade": "C", "suggestions": []}
        s = make_sensor(data)
        assert s.extra_state_attributes["suggestions"] == []

    def test_ci4_reading_missing_raw_value(self):
        data = {
            "ok": True, "score": 75.0, "grade": "B",
            "readings": [
                {"factor": "temperature", "score": 80, "status": "good", "raw_value": None},
            ],
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["temperature_score"] == 80
        assert "temperature_value" not in attrs

    def test_ci4_reading_no_status(self):
        data = {
            "ok": True, "score": 75.0,
            "readings": [{"factor": "humidity", "score": 60}],
        }
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert attrs["humidity_score"] == 60

    def test_ci4_zone_id_missing(self):
        data = {"ok": True, "score": 80.0, "grade": "B"}
        s = make_sensor(data)
        assert "zone_id" not in s.extra_state_attributes

    def test_ci4_not_ok(self):
        data = {"ok": False, "score": 99.0}
        s = make_sensor(data)
        assert s.native_value is None
        assert s.icon == "mdi:home-thermometer"

    def test_ci4_score_zero(self):
        data = {"ok": True, "score": 0.0, "grade": "F"}
        s = make_sensor(data)
        assert s.native_value == 0.0
        assert s.icon == "mdi:emoticon-dead"


# ─── GC1-GC2: global contract ───────────────────────────────────────────────

class TestCIGlobalContract:
    """Global contract: hits /api/v1/comfort, no local semantic invention."""

    def test_gc1_api_endpoint(self):
        # Verify sensor builds URL from _core_base_url()
        data = {"ok": True, "score": 80.0, "grade": "C"}
        s = make_sensor(data)
        attrs = s.extra_state_attributes
        assert "comfort_url" in attrs
        assert "/api/v1/comfort" in attrs["comfort_url"]
        assert "lighting_url" in attrs
        assert "/api/v1/comfort/lighting" in attrs["lighting_url"]

    def test_gc2_no_local_semantic_invention(self):
        # Score and grade are never computed locally — mirror API verbatim
        data = {"ok": True, "score": 0.0, "grade": "F"}
        s = make_sensor(data)
        assert s.native_value == 0.0
        assert s.icon == "mdi:emoticon-dead"

        data = {"ok": True, "score": 100.0, "grade": "A"}
        s._comfort_data = data
        assert s.native_value == 100.0
        assert s.icon == "mdi:emoticon-happy"
