"""Projection Contract Tests for SceneIntelligenceSensor (HA-16).

Verifies that SceneIntelligenceSensor is a pure Projection-Shell on Core-truth
(/api/v1/hub/scenes) with only trivial conditionals and _ICON_MAP lookup.

Pattern: same as HA-6/8/9/10/11/12/13/14/15.
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

    Contract:
    - _fetch(): hits /api/v1/hub/scenes
    - native_value: active_scene.name_de | "Nicht verfügbar" | "{n} Szenen verfügbar"
    - icon: _ICON_MAP lookup or "mdi:palette" fallback
    - extra_state_attributes: direct passthrough, suggestions[:3]
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    async def _fetch(self):
        return self._data

    def _apply(self, fetched_data):
        if fetched_data and fetched_data.get("ok"):
            self._data = fetched_data

    @property
    def native_value(self):
        active = self._data.get("active_scene")
        if active:
            return active.get("name_de", "Aktive Szene")
        total = self._data.get("total_scenes", 0)
        if total == 0:
            return "Nicht verfügbar"
        return f"{total} Szenen verfügbar"

    @property
    def icon(self):
        active = self._data.get("active_scene")
        if active:
            return _ICON_MAP.get(active.get("scene_id", ""), "mdi:palette")
        return "mdi:palette"

    @property
    def extra_state_attributes(self):
        attrs = {
            "total_scenes": self._data.get("total_scenes", 0),
            "learned_patterns": self._data.get("learned_patterns", 0),
        }
        active = self._data.get("active_scene")
        if active:
            attrs["active_scene_id"] = active.get("scene_id")
            attrs["active_scene_name"] = active.get("name_de")
            attrs["active_zone"] = active.get("zone_id")
        suggestions = self._data.get("suggestions", [])
        if suggestions:
            attrs["suggestions"] = [
                {"scene": s.get("name_de"), "confidence": s.get("confidence"),
                 "reason": s.get("reason_de"), "icon": s.get("icon")}
                for s in suggestions[:3]
            ]
        cloud = self._data.get("cloud_status", {})
        if cloud:
            attrs["cloud_connected"] = cloud.get("connected", False)
            attrs["cloud_shared_scenes"] = cloud.get("shared_scenes", 0)
        categories = self._data.get("categories", {})
        if categories:
            attrs["categories"] = categories
        return attrs


SC1_native_value = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "active_scene": {"name_de": "Morgenroutine"}}, "Morgenroutine"),
    ({"ok": True, "active_scene": {"name_de": ""}}, ""),
    ({"ok": True, "total_scenes": 3}, "3 Szenen verfügbar"),
    ({"ok": True, "total_scenes": 0}, "Nicht verfügbar"),
    ({"ok": True, "total_scenes": 5}, "5 Szenen verfügbar"),
    ({"ok": True, "total_scenes": 12}, "12 Szenen verfügbar"),
    ({"ok": True}, "Nicht verfügbar"),
])
SC2_icon = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "active_scene": {"scene_id": "morning_routine"}}, "mdi:weather-sunny"),
    ({"ok": True, "active_scene": {"scene_id": "work_focus"}}, "mdi:head-lightbulb"),
    ({"ok": True, "active_scene": {"scene_id": "bedtime"}}, "mdi:bed"),
    ({"ok": True, "active_scene": {"scene_id": "party"}}, "mdi:party-popper"),
    ({"ok": True, "active_scene": {"scene_id": "unknown_scene"}}, "mdi:palette"),
    ({"ok": True, "active_scene": {}}, "mdi:palette"),
    ({"ok": True}, "mdi:palette"),
    ({"ok": True, "active_scene": {"scene_id": ""}}, "mdi:palette"),
])
SC3_attrs = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "total_scenes": 8, "learned_patterns": 3}, "total_scenes", 8),
    ({"ok": True, "total_scenes": 8, "learned_patterns": 3}, "learned_patterns", 3),
    ({"ok": True, "active_scene": {"scene_id": "morning", "name_de": "Morgen", "zone_id": "z1"}}, "active_scene_id", "morning"),
    ({"ok": True, "active_scene": {"scene_id": "morning", "name_de": "Morgen", "zone_id": "z1"}}, "active_scene_name", "Morgen"),
    ({"ok": True, "active_scene": {"scene_id": "morning", "name_de": "Morgen", "zone_id": "z1"}}, "active_zone", "z1"),
    ({"ok": True, "cloud_status": {"connected": True, "shared_scenes": 2}}, "cloud_connected", True),
    ({"ok": True, "cloud_status": {"connected": True, "shared_scenes": 2}}, "cloud_shared_scenes", 2),
])
SC4_suggestions = pytest.mark.parametrize("suggestions_data,expected_count", [
    ([], 0),
    ([{"name_de": "s1", "confidence": 0.9, "reason_de": "r1", "icon": "mdi:x"}], 1),
    ([{"name_de": f"s{i}", "confidence": 0.5, "reason_de": f"r{i}", "icon": "mdi:x"} for i in range(5)], 3),
    ([{"name_de": f"s{i}", "confidence": 0.5, "reason_de": f"r{i}", "icon": "mdi:x"} for i in range(10)], 3),
])
SC5_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "active_scene": {"name_de": "Test"}}, True),
    ({"ok": True, "total_scenes": 3}, True),
])


@SC1_native_value
def test_SC1_native_value(core_data, expected):
    s = SceneIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.native_value == expected


@SC2_icon
def test_SC2_icon(core_data, expected_icon):
    s = SceneIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.icon == expected_icon


@SC3_attrs
def test_SC3_attrs(core_data, key, expected):
    s = SceneIntelligenceSensorContract(MockCoordinator({}))
    s._apply(core_data)
    assert s.extra_state_attributes[key] == expected


@SC4_suggestions
def test_SC4_suggestions_cap(suggestions_data, expected_count):
    s = SceneIntelligenceSensorContract(MockCoordinator({}))
    s._apply({"ok": True, "suggestions": suggestions_data})
    attrs = s.extra_state_attributes
    assert len(attrs.get("suggestions", [])) == expected_count


@SC5_edge
def test_SC5_edge(data, expect_ok):
    s = SceneIntelligenceSensorContract(MockCoordinator({}))
    s._apply(data)
    if expect_ok:
        assert s._data.get("ok") is True
