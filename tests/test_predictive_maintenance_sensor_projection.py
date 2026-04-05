"""Projection Contract Tests for PredictiveMaintenanceSensor (HA-44).

Pure Projection-Shell on Core-truth (/api/v1/hub).
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


class PredictiveMaintenanceSensorContract:
    """Mirror of PredictiveMaintenanceSensor projection logic.

    Contract:
    - hits /api/v1/hub (summary endpoint)
    - native_value: avg_health_score
    - icon: mdi:wrench-clock (critical) | mdi:wrench (warning) | mdi:wrench-cog (ok)
    - extra_state_attributes: device health passthrough
    """
    def __init__(self):
        self._summary = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._summary = data

    @property
    def native_value(self):
        return self._summary.get("avg_health_score")

    @property
    def icon(self):
        critical = self._summary.get("critical", 0)
        warning = self._summary.get("warning", 0)
        if critical > 0:
            return "mdi:wrench-clock"
        elif warning > 0:
            return "mdi:wrench"
        return "mdi:wrench-cog"

    @property
    def extra_state_attributes(self):
        return {
            "critical": self._summary.get("critical", 0),
            "warning": self._summary.get("warning", 0),
            "devices_checked": self._summary.get("devices_checked", 0),
            "last_check": self._summary.get("last_check"),
        }


# ── Tests ─────────────────────────────────────────────────────────────────

def test_PM1_native_value():
    s = PredictiveMaintenanceSensorContract()
    s.apply({"ok": True, "avg_health_score": 92.5})
    assert s.native_value == 92.5

def test_PM2_native_value_none():
    s = PredictiveMaintenanceSensorContract()
    s.apply({})
    assert s.native_value is None

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "critical": 1, "warning": 0}, "mdi:wrench-clock"),
    ({"ok": True, "critical": 0, "warning": 3}, "mdi:wrench"),
    ({"ok": True, "critical": 0, "warning": 0}, "mdi:wrench-cog"),
    ({"ok": True, "critical": 0, "warning": -1}, "mdi:wrench-cog"),
    ({}, "mdi:wrench-cog"),
])
def test_PM3_icon(data, expected_icon):
    s = PredictiveMaintenanceSensorContract()
    s.apply(data)
    assert s.icon == expected_icon

def test_PM4_attrs():
    s = PredictiveMaintenanceSensorContract()
    s.apply({"ok": True, "avg_health_score": 88.0, "critical": 1, "warning": 2, "devices_checked": 15, "last_check": "2026-04-05T10:00:00Z"})
    attrs = s.extra_state_attributes
    assert attrs["critical"] == 1
    assert attrs["warning"] == 2
    assert attrs["devices_checked"] == 15
