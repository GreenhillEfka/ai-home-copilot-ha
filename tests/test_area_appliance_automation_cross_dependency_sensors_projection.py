"""Projection Contract Tests for 6 more sensors (HA-38 through HA-43).

area_presence_sensor: hybrid (HA-local + Core sync) — tested for Core-sync contract only.
All others: pure Projection-Shells on Core API.
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data=None):
        self.data = data or {}
        self.hass = MockHass()
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"
        self._session = Mock()


# ── ApplianceFingerprintSensor ─────────────────────────────────────────────

class ApplianceFingerprintSensorContract:
    """hits /api/v1/energy (appliance fingerprint)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("total_appliances", 0)
    @property
    def extra_state_attributes(self):
        return {
            "appliances": self._data.get("appliances", [])[:20],
            "total_power_w": self._data.get("total_power_w"),
        }


# ── AutomationSuggestionSensor ─────────────────────────────────────────────

class AutomationSuggestionSensorContract:
    """hits /api/v1/automations/suggestions"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("suggestion_count", 0)
    @property
    def extra_state_attributes(self):
        return {
            "suggestions": self._data.get("suggestions", [])[:10],
            "automation_count": self._data.get("automation_count", 0),
        }


# ── AutomationTemplateSensor ───────────────────────────────────────────────

class AutomationTemplateSensorContract:
    """hits /api/v1/hub/templates/summary"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("template_count", 0)
    @property
    def extra_state_attributes(self):
        return {
            "templates": self._data.get("templates", [])[:10],
            "categories": self._data.get("categories", []),
        }


# ── CrossDependencySensor ─────────────────────────────────────────────────

class CrossDependencySensorContract:
    """hits /api/v1/graph/state + /api/v1/suggestions/repairs"""
    def __init__(self):
        self._graph_data = {}
        self._suggestions_data = {}
    def apply_graph(self, data):
        if data and data.get("ok"):
            self._graph_data = data
    def apply_suggestions(self, data):
        if data and data.get("ok"):
            self._suggestions_data = data
    @property
    def native_value(self):
        return self._graph_data.get("node_count", 0)
    @property
    def extra_state_attributes(self):
        return {
            "node_count": self._graph_data.get("node_count", 0),
            "edge_count": self._graph_data.get("edge_count", 0),
            "repair_suggestions": self._suggestions_data.get("suggestions", [])[:5],
        }


# ── AreaPresenceSensor — Core-sync contract only ───────────────────────────

class AreaPresenceSensorSyncContract:
    """Mirrors the Core-sync contract of AreaPresenceSensor.

    Contract: when Core sync succeeds, zone states come from
    /api/v1/zone-automation/dashboard. This is the ONLY part we test here.
    The HA-local sensor fusion (mmWave/PIR/BLE/person) is NOT a projection
    contract — skip it for contract-testing purposes.
    """
    def __init__(self):
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def synced_zones(self):
        return self._data.get("zones", [])

    @property
    def zone_states(self):
        return {z.get("zone_id"): z.get("primary_state") for z in self._data.get("zones", [])}


# ── Tests: ApplianceFingerprintSensor ───────────────────────────────────

def test_AP1_native_value():
    s = ApplianceFingerprintSensorContract()
    s.apply({"ok": True, "total_appliances": 8, "appliances": [{"id": "dishwasher"}], "total_power_w": 2500})
    assert s.native_value == 8

def test_AP2_attrs():
    s = ApplianceFingerprintSensorContract()
    s.apply({"ok": True, "total_appliances": 3, "appliances": [{"id": "a"}], "total_power_w": 500})
    attrs = s.extra_state_attributes
    assert len(attrs["appliances"]) == 1
    assert attrs["total_power_w"] == 500


# ── Tests: AutomationSuggestionSensor ────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "suggestion_count": 5, "suggestions": [], "automation_count": 10}, 5),
    ({"ok": True, "suggestion_count": 0}, 0),
    ({}, 0),
])
def test_AS1_native_value(data, expected):
    s = AutomationSuggestionSensorContract()
    s.apply(data)
    assert s.native_value == expected

def test_AS2_attrs():
    s = AutomationSuggestionSensorContract()
    s.apply({"ok": True, "suggestion_count": 2, "suggestions": [{"id": "s1"}, {"id": "s2"}], "automation_count": 10})
    attrs = s.extra_state_attributes
    assert len(attrs["suggestions"]) == 2


# ── Tests: AutomationTemplateSensor ──────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "template_count": 12, "templates": [], "categories": []}, 12),
    ({"ok": True, "template_count": 0}, 0),
    ({}, 0),
])
def test_AT1_native_value(data, expected):
    s = AutomationTemplateSensorContract()
    s.apply(data)
    assert s.native_value == expected

def test_AT2_attrs():
    s = AutomationTemplateSensorContract()
    s.apply({"ok": True, "template_count": 3, "templates": [{"id": "t1"}], "categories": ["energy", "presence"]})
    attrs = s.extra_state_attributes
    assert attrs["categories"] == ["energy", "presence"]


# ── Tests: CrossDependencySensor ────────────────────────────────────────

def test_CD1_native_value():
    s = CrossDependencySensorContract()
    s.apply_graph({"ok": True, "node_count": 42, "edge_count": 87})
    assert s.native_value == 42

def test_CD2_attrs():
    s = CrossDependencySensorContract()
    s.apply_graph({"ok": True, "node_count": 10, "edge_count": 25})
    s.apply_suggestions({"ok": True, "suggestions": [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]})
    attrs = s.extra_state_attributes
    assert attrs["node_count"] == 10
    assert attrs["edge_count"] == 25
    assert len(attrs["repair_suggestions"]) == 3


# ── Tests: AreaPresenceSensor Core-sync contract ─────────────────────────

def test_AREA1_zones_from_core():
    """When Core sync is active, zones come from /api/v1/zone-automation/dashboard."""
    s = AreaPresenceSensorSyncContract()
    s.apply({
        "ok": True,
        "zones": [
            {"zone_id": "living_room", "primary_state": "occupied"},
            {"zone_id": "bedroom", "primary_state": "vacant"},
        ]
    })
    assert len(s.synced_zones) == 2
    assert s.zone_states["living_room"] == "occupied"
    assert s.zone_states["bedroom"] == "vacant"

def test_AREA2_empty():
    s = AreaPresenceSensorSyncContract()
    s.apply({"ok": True, "zones": []})
    assert s.synced_zones == []
    assert s.zone_states == {}

def test_AREA3_edge_no_ok():
    s = AreaPresenceSensorSyncContract()
    s.apply({})
    assert s.synced_zones == []
