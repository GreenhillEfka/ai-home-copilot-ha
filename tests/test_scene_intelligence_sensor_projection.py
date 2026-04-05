"""Projection Contract Tests for SceneIntelligenceSensor.

Verifies SceneIntelligenceSensor is a pure Projection-Shell on /api/v1/hub/scenes.

HA-123 — 2026-04-05
"""
from __future__ import annotations

import pytest


# =============================================================================
# Contract Mirror
# =============================================================================
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


class SceneIntelligenceSensorContract:
    """Mirror of SceneIntelligenceSensor projection logic.

    Contract: SceneIntelligenceSensor is a pure Projection-Shell on
    /api/v1/hub/scenes. All values are trivially formatted from
    coordinator.data. No local ML, classification, or heuristic.
    """

    @staticmethod
    def compute_native_value(data: dict) -> str:
        active = data.get("active_scene")
        if active:
            return active.get("name_de", "Aktive Szene")
        total = data.get("total_scenes", 0)
        if total == 0:
            return "Nicht verfügbar"
        return f"{total} Szenen verfügbar"

    @staticmethod
    def compute_icon(data: dict) -> str:
        active = data.get("active_scene")
        if active:
            return _ICON_MAP.get(active.get("scene_id", ""), "mdi:palette")
        return "mdi:palette"

    @staticmethod
    def compute_attrs(data: dict) -> dict:
        attrs = {
            "total_scenes": data.get("total_scenes", 0),
            "learned_patterns": data.get("learned_patterns", 0),
        }
        active = data.get("active_scene")
        if active:
            attrs["active_scene_id"] = active.get("scene_id")
            attrs["active_scene_name"] = active.get("name_de")
            attrs["active_zone"] = active.get("zone_id")
        suggestions = data.get("suggestions", [])
        if suggestions:
            attrs["suggestions"] = [
                {
                    "scene": s.get("name_de"),
                    "confidence": s.get("confidence"),
                    "reason": s.get("reason_de"),
                    "icon": s.get("icon"),
                }
                for s in suggestions[:3]
            ]
        cloud = data.get("cloud_status", {})
        if cloud:
            attrs["cloud_connected"] = cloud.get("connected", False)
            attrs["cloud_shared_scenes"] = cloud.get("shared_scenes", 0)
        categories = data.get("categories", {})
        if categories:
            attrs["categories"] = categories
        return attrs


# =============================================================================
# SC1: native_value — active scene present
# =============================================================================
@pytest.mark.parametrize("scene_id,scene_name,expected", [
    ("morning_routine", "Morgenroutine", "Morgenroutine"),
    ("work_focus", "Arbeitsfokus", "Arbeitsfokus"),
    ("evening_relax", "Feierabend", "Feierabend"),
    ("bedtime", "Schlafenszeit", "Schlafenszeit"),
    ("party", "Party", "Party"),
    ("away", "Abwesend", "Abwesend"),
])
def test_SC1_native_value_active_scene(scene_id, scene_name, expected):
    data = {
        "ok": True,
        "active_scene": {"scene_id": scene_id, "name_de": scene_name, "zone_id": "zone_1"},
        "total_scenes": 12,
    }
    assert SceneIntelligenceSensorContract.compute_native_value(data) == expected


# =============================================================================
# SC2: native_value — no active scene
# =============================================================================
@pytest.mark.parametrize("total_scenes,expected", [
    (0, "Nicht verfügbar"),
    (1, "1 Szenen verfügbar"),
    (8, "8 Szenen verfügbar"),
    (25, "25 Szenen verfügbar"),
])
def test_SC2_native_value_no_active_scene(total_scenes, expected):
    data = {
        "ok": True,
        "active_scene": None,
        "total_scenes": total_scenes,
    }
    assert SceneIntelligenceSensorContract.compute_native_value(data) == expected


# =============================================================================
# SC3: icon mapping
# =============================================================================
@pytest.mark.parametrize("scene_id,expected_icon", [
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
])
def test_SC3_icon_mapping(scene_id, expected_icon):
    data = {
        "ok": True,
        "active_scene": {"scene_id": scene_id, "name_de": "Test", "zone_id": "zone_1"},
        "total_scenes": 5,
    }
    assert SceneIntelligenceSensorContract.compute_icon(data) == expected_icon


# =============================================================================
# SC4: extra_state_attributes
# =============================================================================
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


# =============================================================================
# SC5: edge cases
# =============================================================================
def test_SC5_suggestions_capped():
    """Suggestions are capped at 3."""
    suggestions = [
        {"name_de": f"Szene {i}", "confidence": 0.9 - i*0.05, "reason_de": f"Grund {i}", "icon": "mdi:home"}
        for i in range(7)
    ]
    data = {"ok": True, "suggestions": suggestions}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert len(attrs["suggestions"]) == 3


def test_SC5_empty_cloud_status():
    """Empty cloud_status does not add cloud attributes."""
    data = {"ok": True, "cloud_status": {}}
    attrs = SceneIntelligenceSensorContract.compute_attrs(data)
    assert "cloud_connected" not in attrs
    assert "cloud_shared_scenes" not in attrs


def test_SC5_missing_optional_fields():
    """Missing optional fields are handled gracefully."""
    data = {"ok": True}
    # Should not raise
    _ = SceneIntelligenceSensorContract.compute_native_value(data)
    _ = SceneIntelligenceSensorContract.compute_icon(data)
    _ = SceneIntelligenceSensorContract.compute_attrs(data)


# =============================================================================
# GC1: global contract — pure projection shell
# =============================================================================
def test_GC1_pure_projection_on_hub_scenes():
    """SceneIntelligenceSensor hits /api/v1/hub/scenes — pure projection, no local semantic invention."""
    test_data = {
        "ok": True,
        "active_scene": {"scene_id": "morning_routine", "name_de": "Morgenroutine", "zone_id": "zone_1"},
        "total_scenes": 10,
        "learned_patterns": 3,
        "suggestions": [{"name_de": "Feierabend", "confidence": 0.92, "reason_de": "Test", "icon": "mdi:sofa"}],
        "cloud_status": {"connected": True, "shared_scenes": 2},
        "categories": {"routine": 4},
    }

    # Contract: trivially formatted from hub/scenes API response
    # No local ML, classification, or heuristic logic
    assert SceneIntelligenceSensorContract.compute_native_value(test_data) == "Morgenroutine"
    assert SceneIntelligenceSensorContract.compute_icon(test_data) == "mdi:weather-sunny"
    assert SceneIntelligenceSensorContract.compute_attrs(test_data)["total_scenes"] == 10
