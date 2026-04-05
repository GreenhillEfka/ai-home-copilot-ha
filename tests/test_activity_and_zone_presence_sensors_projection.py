"""Projection Contract Tests for ActivitySensors and ZonePresenceTriggerSensor (HA-47).

activity_sensors: pure Projection-Shells on /api/v1/neurons
zone_presence_trigger: pure Projection-Shell on /api/v1/zone-automation/dashboard
Final pure-projection coverage batch.
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


# ── ActivityLevelSensor contract ───────────────────────────────────────────

class ActivityLevelSensorContract:
    """Mirror of ActivityLevelSensor — hits /api/v1/neurons (activity data)."""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        activity = self._data.get("activity", {})
        return activity.get("level", "unknown")
    @property
    def extra_state_attributes(self):
        activity = self._data.get("activity", {})
        return {
            "level": activity.get("level", "unknown"),
            "score": activity.get("score", 0),
            "change_pct": activity.get("change_pct", 0),
            "last_update": activity.get("last_update"),
        }


# ── ActivityStillnessSensor contract ──────────────────────────────────────

class ActivityStillnessSensorContract:
    """Mirror of ActivityStillnessSensor — stillness detection from /api/v1/neurons."""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        stillness = self._data.get("stillness", {})
        return stillness.get("detected", False)
    @property
    def extra_state_attributes(self):
        stillness = self._data.get("stillness", {})
        return {
            "detected": stillness.get("detected", False),
            "duration_sec": stillness.get("duration_sec", 0),
            "confidence": stillness.get("confidence", 0.0),
        }


# ── ZonePresenceTriggerSensor contract ─────────────────────────────────────

class ZonePresenceTriggerSensorContract:
    """Mirror of ZonePresenceTriggerSensor — hits /api/v1/zone-automation/dashboard."""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        count = len(self._data.get("zones", []))
        return count
    @property
    def extra_state_attributes(self):
        zones = self._data.get("zones", [])
        return {
            "zone_count": len(zones),
            "occupied_zones": sum(1 for z in zones if z.get("state") == "occupied"),
            "vacant_zones": sum(1 for z in zones if z.get("state") == "vacant"),
            "zones": [{"id": z.get("zone_id"), "state": z.get("state")} for z in zones[:10]],
        }


# ── Tests: ActivityLevelSensor ─────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "activity": {"level": "high", "score": 85, "change_pct": 12.5, "last_update": "2026-04-05T10:00:00Z"}}, "high"),
    ({"ok": True, "activity": {"level": "low"}}, "low"),
    ({"ok": True, "activity": {}}, "unknown"),
    ({}, "unknown"),
])
def test_AL1_native_value(data, expected):
    s = ActivityLevelSensorContract()
    s.apply(data)
    assert s.native_value == expected

def test_AL2_attrs():
    s = ActivityLevelSensorContract()
    s.apply({"ok": True, "activity": {"level": "medium", "score": 55, "change_pct": -5.2, "last_update": "2026-04-05T12:00:00Z"}})
    attrs = s.extra_state_attributes
    assert attrs["score"] == 55
    assert attrs["change_pct"] == -5.2


# ── Tests: ActivityStillnessSensor ─────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "stillness": {"detected": True, "duration_sec": 120, "confidence": 0.92}}, True),
    ({"ok": True, "stillness": {"detected": False}}, False),
    ({}, False),
])
def test_AS1_native_value(data, expected):
    s = ActivityStillnessSensorContract()
    s.apply(data)
    assert s.native_value == expected

def test_AS2_attrs():
    s = ActivityStillnessSensorContract()
    s.apply({"ok": True, "stillness": {"detected": True, "duration_sec": 300, "confidence": 0.88}})
    attrs = s.extra_state_attributes
    assert attrs["detected"] is True
    assert attrs["duration_sec"] == 300
    assert attrs["confidence"] == 0.88


# ── Tests: ZonePresenceTriggerSensor ───────────────────────────────────────

def test_ZP1_native_value():
    s = ZonePresenceTriggerSensorContract()
    s.apply({"ok": True, "zones": [{"zone_id": "z1", "state": "occupied"}, {"zone_id": "z2", "state": "vacant"}, {"zone_id": "z3", "state": "occupied"}]})
    assert s.native_value == 3

def test_ZP2_counts():
    s = ZonePresenceTriggerSensorContract()
    s.apply({"ok": True, "zones": [{"zone_id": "z1", "state": "occupied"}, {"zone_id": "z2", "state": "occupied"}, {"zone_id": "z3", "state": "vacant"}]})
    attrs = s.extra_state_attributes
    assert attrs["occupied_zones"] == 2
    assert attrs["vacant_zones"] == 1

def test_ZP3_zone_list():
    s = ZonePresenceTriggerSensorContract()
    zones = [{"zone_id": f"z{i}", "state": "occupied"} for i in range(15)]
    s.apply({"ok": True, "zones": zones})
    attrs = s.extra_state_attributes
    assert len(attrs["zones"]) == 10  # capped at 10
    assert attrs["zone_count"] == 15

def test_ZP4_empty():
    s = ZonePresenceTriggerSensorContract()
    s.apply({"ok": True, "zones": []})
    attrs = s.extra_state_attributes
    assert attrs["zone_count"] == 0
    assert attrs["occupied_zones"] == 0
