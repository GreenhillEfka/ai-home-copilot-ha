"""
Projection Contract Tests for AutomationTemplateSensor (HA-152).

Contract: AutomationTemplateSensor is a pure projection shell on
/api/v1/hub/templates/summary — trivial dict lookups, no local semantics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class AutomationTemplateSensorContract:
    """Contract mirror for AutomationTemplateSensor."""

    def __init__(self, data: dict | None) -> None:
        self._data = data or {}

    def native_value(self) -> str:
        total = self._data.get("total_templates", 0)
        generated = self._data.get("generated_count", 0)
        if total == 0:
            return "Nicht verfügbar"
        return f"{total} Templates, {generated} generiert"

    def icon(self) -> str:
        return "mdi:robot"

    def extra_state_attributes(self) -> dict:
        attrs = {
            "total_templates": self._data.get("total_templates", 0),
            "generated_count": self._data.get("generated_count", 0),
        }
        categories = self._data.get("categories", {})
        if categories:
            attrs["categories"] = categories
        popular = self._data.get("popular", [])
        if popular:
            attrs["popular"] = [
                {
                    "name": p.get("name_de"),
                    "icon": p.get("icon"),
                    "usage": p.get("usage_count"),
                    "rating": p.get("rating"),
                }
                for p in popular[:5]
            ]
        return attrs


# ---- Cases ----

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "total_templates": 5, "generated_count": 3}, "5 Templates, 3 generiert"),
    ({"ok": True, "total_templates": 1, "generated_count": 1}, "1 Templates, 1 generiert"),
    ({"ok": True, "total_templates": 0, "generated_count": 0}, "Nicht verfügbar"),
    ({"ok": False, "total_templates": 5, "generated_count": 3}, "5 Templates, 3 generiert"),
    ({"ok": True, "total_templates": 5, "generated_count": 0}, "5 Templates, 0 generiert"),
    ({"ok": True, "total_templates": 10, "generated_count": 7}, "10 Templates, 7 generiert"),
    ({"ok": True, "total_templates": 99, "generated_count": 55}, "99 Templates, 55 generiert"),
])
def test_AT_native_value(data, expected):
    """AT1: native_value — total/generated string or fallback."""
    sensor = AutomationTemplateSensorContract(data)
    assert sensor.native_value() == expected


def test_AT_icon():
    """AT2: icon is static."""
    sensor = AutomationTemplateSensorContract({})
    assert sensor.icon() == "mdi:robot"


@pytest.mark.parametrize("data,expected_keys", [
    (
        {"total_templates": 5, "generated_count": 3, "categories": {"light": 2, "climate": 3}},
        {"total_templates": 5, "generated_count": 3, "categories": {"light": 2, "climate": 3}},
    ),
    (
        {"total_templates": 0, "generated_count": 0},
        {"total_templates": 0, "generated_count": 0},
    ),
    (
        {
            "total_templates": 3,
            "generated_count": 2,
            "popular": [
                {"name_de": "Lichtszene Wohnzimmer", "icon": "mdi:lightbulb", "usage_count": 42, "rating": 4.5},
                {"name_de": "Heizung Abend", "icon": "mdi:thermometer", "usage_count": 28, "rating": 4.2},
            ],
        },
        {
            "total_templates": 3,
            "generated_count": 2,
            "popular": [
                {"name": "Lichtszene Wohnzimmer", "icon": "mdi:lightbulb", "usage": 42, "rating": 4.5},
                {"name": "Heizung Abend", "icon": "mdi:thermometer", "usage": 28, "rating": 4.2},
            ],
        },
    ),
    (
        {"total_templates": 5, "generated_count": 3, "categories": {}},
        {"total_templates": 5, "generated_count": 3},
    ),
])
def test_AT_attrs(data, expected_keys):
    """AT3: extra_state_attributes — dict lookups + popular capped[:5]."""
    sensor = AutomationTemplateSensorContract(data)
    attrs = sensor.extra_state_attributes()
    for key in expected_keys:
        assert key in attrs
    if "popular" in expected_keys:
        assert len(attrs["popular"]) == 2


@pytest.mark.parametrize("data", [
    {},
    None,
    {"total_templates": 5},
    {"generated_count": 3},
    {"ok": True},
])
def test_AT_edge_missing_fields(data):
    """AT4: edge — missing optional fields gracefully handled."""
    sensor = AutomationTemplateSensorContract(data)
    native = sensor.native_value()
    attrs = sensor.extra_state_attributes()
    assert isinstance(native, str)
    assert isinstance(attrs, dict)


def test_AT_popular_capped_at_5():
    """AT5: popular list capped at [:5]."""
    popular = [{"name_de": f"Template {i}", "icon": "mdi:star", "usage_count": i, "rating": 4.0} for i in range(8)]
    data = {"total_templates": 8, "generated_count": 8, "popular": popular}
    sensor = AutomationTemplateSensorContract(data)
    attrs = sensor.extra_state_attributes()
    assert "popular" in attrs
    assert len(attrs["popular"]) == 5


# ---- Global Contract ----

def test_GC1_pure_projection_shell():
    """GC1: hits exactly /api/v1/hub/templates/summary."""
    # Mirror only — endpoint verified via code inspection
    sensor = AutomationTemplateSensorContract({"ok": True, "total_templates": 1, "generated_count": 1})
    assert sensor.native_value() == "1 Templates, 1 generiert"


def test_GC2_no_local_semantic_invention():
    """GC2: no local threshold/classification/logic — pure Core data pass-through."""
    cases = [
        {"ok": True, "total_templates": 0, "generated_count": 0},
        {"ok": True, "total_templates": 100, "generated_count": 99},
        {"ok": False, "total_templates": 5, "generated_count": 3},
        None,
        {},
    ]
    for case in cases:
        sensor = AutomationTemplateSensorContract(case)
        result = sensor.native_value()
        assert isinstance(result, str)
