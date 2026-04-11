"""Projection Contract Tests for SceneIntelligenceSensor.

Verifies SceneIntelligenceSensor is a pure projection shell on
/api/v1/hub/scenes.

HA-123, HA-342
"""

from __future__ import annotations

from pathlib import Path
import math

import pytest


_ICON_MAP = {
    "morning_routine": "mdi:weather-sunny",
    "work_focus": "mdi:head-lightbulb",
    "lunch_break": "mdi:food",
    "afternoon_relax": "mdi:sofa",
    "dinner_time": "mdi:silverware-fork-knife",
    "movie_night": "mdi:movie-open",
    "romantic_evening": "mdi:heart",
    "bedtime": "mdi:bed",
    "party": "mdi:party-popper",
    "away": "mdi:home-export-outline",
}


def _as_mapping(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _as_int(value, default):
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _as_float(value, default):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        numeric_value = float(value)
        return numeric_value if math.isfinite(numeric_value) else default
    return default


def _as_string(value, default=""):
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default


def _as_bool(value, default=False):
    if isinstance(value, bool):
        return value
    return default


class SceneIntelligenceSensorContract:
    """Mirror of SceneIntelligenceSensor projection logic."""

    @staticmethod
    def compute_native_value(data: dict) -> str:
        active = _as_mapping(data.get("active_scene"))
        if active:
            return _as_string(active.get("name_de"), "Aktive Szene")
        total = _as_int(data.get("total_scenes"), 0)
        if total == 0:
            return "Nicht verfügbar"
        return f"{total} Szenen verfügbar"

    @staticmethod
    def compute_icon(data: dict) -> str:
        active = _as_mapping(data.get("active_scene"))
        if active:
            return _ICON_MAP.get(_as_string(active.get("scene_id")), "mdi:palette")
        return "mdi:palette"

    @staticmethod
    def compute_attrs(data: dict) -> dict:
        attrs = {
            "total_scenes": _as_int(data.get("total_scenes"), 0),
            "learned_patterns": _as_int(data.get("learned_patterns"), 0),
        }

        active = _as_mapping(data.get("active_scene"))
        if active:
            scene_id = _as_string(active.get("scene_id"))
            scene_name = _as_string(active.get("name_de"))
            zone_id = _as_string(active.get("zone_id"))
            if scene_id:
                attrs["active_scene_id"] = scene_id
            if scene_name:
                attrs["active_scene_name"] = scene_name
            if zone_id:
                attrs["active_zone"] = zone_id

        suggestions = _as_list(data.get("suggestions"))
        if suggestions:
            projected_suggestions = []
            for suggestion in suggestions[:3]:
                if not isinstance(suggestion, dict):
                    continue
                projected_suggestions.append(
                    {
                        "scene": _as_string(suggestion.get("name_de")),
                        "confidence": _as_float(suggestion.get("confidence"), 0.0),
                        "reason": _as_string(suggestion.get("reason_de")),
                        "icon": _as_string(suggestion.get("icon")),
                    }
                )
            if projected_suggestions:
                attrs["suggestions"] = projected_suggestions

        cloud = _as_mapping(data.get("cloud_status"))
        if cloud:
            attrs["cloud_connected"] = _as_bool(cloud.get("connected"), False)
            attrs["cloud_shared_scenes"] = _as_int(cloud.get("shared_scenes"), 0)

        categories = _as_mapping(data.get("categories"))
        if categories:
            attrs["categories"] = categories

        return attrs


@pytest.mark.parametrize(
    "scene_id,scene_name,expected",
    [
        ("morning_routine", "Morgenroutine", "Morgenroutine"),
        ("work_focus", "Arbeitsfokus", "Arbeitsfokus"),
        ("bedtime", "Schlafenszeit", "Schlafenszeit"),
        ("party", "Party", "Party"),
        ("away", "Abwesend", "Abwesend"),
    ],
)
def test_SC1_native_value_active_scene(scene_id, scene_name, expected):
    data = {
        "ok": True,
        "active_scene": {"scene_id": scene_id, "name_de": scene_name, "zone_id": "zone_1"},
        "total_scenes": 12,
    }
    assert SceneIntelligenceSensorContract.compute_native_value(data) == expected


@pytest.mark.parametrize(
    "total_scenes,expected",
    [
        (0, "Nicht verfügbar"),
        (1, "1 Szenen verfügbar"),
        (8, "8 Szenen verfügbar"),
        (25, "25 Szenen verfügbar"),
    ],
)
def test_SC2_native_value_no_active_scene(total_scenes, expected):
    data = {
        "ok": True,
        "active_scene": None,
        "total_scenes": total_scenes,
    }
    assert SceneIntelligenceSensorContract.compute_native_value(data) == expected


@pytest.mark.parametrize(
    "scene_id,expected_icon",
    [
        ("morning_routine", "mdi:weather-sunny"),
        ("work_focus", "mdi:head-lightbulb"),
        ("lunch_break", "mdi:food"),
        ("afternoon_relax", "mdi:sofa"),
        ("dinner_time", "mdi:silverware-fork-knife"),
        ("movie_night", "mdi:movie-open"),
        ("romantic_evening", "mdi:heart"),
        ("bedtime", "mdi:bed"),
        ("party", "mdi:party-popper"),
        ("away", "mdi:home-export-outline"),
        ("unknown_scene_id", "mdi:palette"),
        ("", "mdi:palette"),
    ],
)
def test_SC3_icon_mapping(scene_id, expected_icon):
    data = {
        "ok": True,
        "active_scene": {"scene_id": scene_id, "name_de": "Test", "zone_id": "zone_1"},
        "total_scenes": 5,
    }
    assert SceneIntelligenceSensorContract.compute_icon(data) == expected_icon


def test_SC4_attrs_full():
    data = {
        "ok": True,
        "active_scene": {"scene_id": "morning_routine", "name_de": "Morgenroutine", "zone_id": "zone_kitchen"},
        "total_scenes": 15,
        "learned_patterns": 7,
        "suggestions": [
            {"name_de": "Feierabend", "confidence": 0.92, "reason_de": "Gewohnheit um 18:00", "icon": "mdi:sofa"},
            {"name_de": "Nachtfahrt", "confidence": 0.78, "reason_de": "Wiederholung Do/Fr", "icon": "mdi:moon-waning-crescent"},
        ],
        "cloud_status": {"connected": True, "shared_scenes": 3},
        "categories": {"routine": 5, "entertainment": 4},
    }
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert attrs["total_scenes"] == 15
    assert attrs["learned_patterns"] == 7
    assert attrs["active_scene_id"] == "morning_routine"
    assert attrs["active_scene_name"] == "Morgenroutine"
    assert attrs["active_zone"] == "zone_kitchen"
    assert len(attrs["suggestions"]) == 2
    assert attrs["cloud_connected"] is True
    assert attrs["cloud_shared_scenes"] == 3
    assert attrs["categories"] == {"routine": 5, "entertainment": 4}


def test_SC4_attrs_minimal():
    data = {"ok": True}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert attrs["total_scenes"] == 0
    assert attrs["learned_patterns"] == 0
    assert "active_scene_id" not in attrs
    assert "suggestions" not in attrs


def test_SC5_suggestions_capped():
    suggestions = [
        {"name_de": f"Szene {i}", "confidence": 0.9 - i * 0.05, "reason_de": f"Grund {i}", "icon": "mdi:home"}
        for i in range(7)
    ]
    data = {"ok": True, "suggestions": suggestions}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert len(attrs["suggestions"]) == 3


def test_SC5_empty_cloud_status():
    data = {"ok": True, "cloud_status": {}}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "cloud_connected" not in attrs
    assert "cloud_shared_scenes" not in attrs


def test_SC5_missing_optional_fields():
    data = {"ok": True}
    _ = SceneIntelligenceSensorContract.compute_native_value(data)
    _ = SceneIntelligenceSensorContract.compute_icon(data)
    _ = SceneIntelligenceSensorContract.compute_attrs(data)


def test_SC6_non_mapping_active_scene_falls_back_to_total_scenes():
    data = {"ok": True, "active_scene": "party", "total_scenes": 4}
    assert SceneIntelligenceSensorContract.compute_native_value(data) == "4 Szenen verfügbar"
    assert SceneIntelligenceSensorContract.compute_icon(data) == "mdi:palette"
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "active_scene_id" not in attrs
    assert "active_scene_name" not in attrs
    assert "active_zone" not in attrs


def test_SC6_active_scene_with_malformed_fields_uses_safe_defaults():
    data = {
        "ok": True,
        "active_scene": {"scene_id": 7, "name_de": ["Party"], "zone_id": False},
        "total_scenes": 9,
    }
    assert SceneIntelligenceSensorContract.compute_native_value(data) == "Aktive Szene"
    assert SceneIntelligenceSensorContract.compute_icon(data) == "mdi:palette"
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "active_scene_id" not in attrs
    assert "active_scene_name" not in attrs
    assert "active_zone" not in attrs


def test_SC6_non_list_suggestions_are_ignored():
    data = {"ok": True, "suggestions": "abendroutine"}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "suggestions" not in attrs


def test_SC6_malformed_suggestion_items_are_skipped_or_normalized():
    data = {
        "ok": True,
        "suggestions": [
            None,
            {"name_de": " Feierabend ", "confidence": "0.91", "reason_de": True, "icon": None},
            "invalid",
            {"name_de": "Nachtfahrt", "confidence": float("inf"), "reason_de": "  Wiederholung ", "icon": " mdi:moon "},
        ],
    }
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert attrs["suggestions"] == [
        {"scene": "Feierabend", "confidence": 0.0, "reason": "", "icon": ""},
    ]


@pytest.mark.parametrize(
    "cloud_status",
    [
        "connected",
        [True, 3],
        4,
    ],
)
def test_SC6_non_mapping_cloud_status_is_ignored(cloud_status):
    data = {"ok": True, "cloud_status": cloud_status}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "cloud_connected" not in attrs
    assert "cloud_shared_scenes" not in attrs


def test_SC6_malformed_cloud_status_fields_fall_back_to_safe_defaults():
    data = {"ok": True, "cloud_status": {"connected": "yes", "shared_scenes": "7"}}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert attrs["cloud_connected"] is False
    assert attrs["cloud_shared_scenes"] == 0


@pytest.mark.parametrize("total_scenes", ["8", True, 2.5])
def test_SC6_non_int_total_scenes_defaults_to_not_available(total_scenes):
    data = {"ok": True, "active_scene": None, "total_scenes": total_scenes}
    assert SceneIntelligenceSensorContract.compute_native_value(data) == "Nicht verfügbar"
    assert SceneIntelligenceSensorContract.compute_attrs(data)["total_scenes"] == 0


@pytest.mark.parametrize("learned_patterns", ["4", False, 3.2])
def test_SC6_non_int_learned_patterns_default_zero(learned_patterns):
    data = {"ok": True, "learned_patterns": learned_patterns}
    assert SceneIntelligenceSensorContract.compute_attrs(data)["learned_patterns"] == 0


def test_SC6_non_mapping_categories_are_ignored():
    data = {"ok": True, "categories": "routine"}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "categories" not in attrs


def test_GC1_pure_projection_on_hub_scenes():
    test_data = {
        "ok": True,
        "active_scene": {"scene_id": "morning_routine", "name_de": "Morgenroutine", "zone_id": "zone_1"},
        "total_scenes": 10,
        "learned_patterns": 3,
        "suggestions": [{"name_de": "Feierabend", "confidence": 0.92, "reason_de": "Test", "icon": "mdi:sofa"}],
        "cloud_status": {"connected": True, "shared_scenes": 2},
        "categories": {"routine": 4},
    }

    assert SceneIntelligenceSensorContract.compute_native_value(test_data) == "Morgenroutine"
    assert SceneIntelligenceSensorContract.compute_icon(test_data) == "mdi:weather-sunny"
    assert SceneIntelligenceSensorContract.compute_attrs(test_data)["total_scenes"] == 10


def test_GC2_source_guard_uses_type_safe_helpers_and_top_level_response_guard():
    source = Path(
        "/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/scene_intelligence_sensor.py"
    ).read_text()

    assert "def _as_mapping" in source
    assert "def _as_list" in source
    assert "def _as_int" in source
    assert "def _as_float" in source
    assert "def _as_string" in source
    assert "def _as_bool" in source
    assert "math.isfinite" in source
    assert "if isinstance(data, dict) and data.get(\"ok\")" in source
    assert "active = _as_mapping(self._data.get(\"active_scene\"))" in source
    assert "suggestions = _as_list(self._data.get(\"suggestions\"))" in source
    assert "if not isinstance(suggestion, dict):" in source
    assert "cloud = _as_mapping(self._data.get(\"cloud_status\"))" in source
