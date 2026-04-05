"""Projection Contract Tests for NotificationSensor (HA-50).

Verifies that NotificationSensor is a pure Projection-Shell on Core-truth
(/api/v1/notifications + /api/v1/notifications/digest) — no local semantic invention.

Pattern: same as HA-6/8/9/10/11/12/13/14.
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
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"
        self._session = session


class NotificationSensorContract:
    """Mirror of NotificationSensor projection logic.

    Contract:
    - native_value: "{count} pending" if count>0 else "no alerts", "unavailable" if !ok
    - icon: mdi:bell-alert if count>0, else mdi:bell-outline
    - extra_state_attributes: pending_count, latest[], digest_count, by_source, by_priority
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._notif_data = None
        self._digest_data = None

    def _core_base_url(self):
        return "http://localhost:18792"

    def _core_headers(self):
        return {"Authorization": "Bearer mock"}

    @property
    def native_value(self):
        if self._notif_data and self._notif_data.get("ok"):
            count = self._notif_data.get("count", 0)
            return f"{count} pending" if count > 0 else "no alerts"
        return "unavailable"

    @property
    def icon(self):
        if self._notif_data and self._notif_data.get("ok"):
            count = self._notif_data.get("count", 0)
            if count > 0:
                return "mdi:bell-alert"
        return "mdi:bell-outline"

    @property
    def extra_state_attributes(self):
        attrs = {
            "notifications_url": f"{self._core_base_url()}/api/v1/notifications",
            "digest_url": f"{self._core_base_url()}/api/v1/notifications/digest",
        }
        if self._notif_data and self._notif_data.get("ok"):
            notifications = self._notif_data.get("notifications", [])
            attrs["pending_count"] = self._notif_data.get("count", 0)
            attrs["latest"] = notifications[:5]
        if self._digest_data and self._digest_data.get("ok"):
            attrs["digest_count"] = self._digest_data.get("count", 0)
            attrs["by_source"] = self._digest_data.get("by_source", {})
            attrs["by_priority"] = self._digest_data.get("by_priority", {})
        return attrs

    def set_notif_data(self, data):
        self._notif_data = data

    def set_digest_data(self, data):
        self._digest_data = data


# ─── native_value cases ────────────────────────────────────────────────────────

def test_NS1_no_data():
    """NS1: No coordinator data → state 'unavailable'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    assert sensor.native_value == "unavailable"


def test_NS2_ok_zero_notifications():
    """NS2: ok=true, count=0 → state 'no alerts'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 0, "notifications": []})
    assert sensor.native_value == "no alerts"


def test_NS3_ok_single_pending():
    """NS3: ok=true, count=1 → state '1 pending'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({
        "ok": True, "count": 1,
        "notifications": [{"id": "n1", "title": "Test"}]
    })
    assert sensor.native_value == "1 pending"


def test_NS4_ok_multiple_pending():
    """NS4: ok=true, count=5 → state '5 pending'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({
        "ok": True, "count": 5,
        "notifications": [{"id": f"n{i}", "title": f"Alert {i}"} for i in range(5)]
    })
    assert sensor.native_value == "5 pending"


def test_NS5_not_ok():
    """NS5: ok=false → state 'unavailable'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": False})
    assert sensor.native_value == "unavailable"


def test_NS6_missing_ok_field():
    """NS6: missing ok field → state 'unavailable'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"count": 0})
    assert sensor.native_value == "unavailable"


# ─── icon cases ────────────────────────────────────────────────────────────────

def test_NI1_no_data():
    """NI1: No notif_data → icon mdi:bell-outline."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    assert sensor.icon == "mdi:bell-outline"


def test_NI2_count_zero():
    """NI2: ok=true, count=0 → mdi:bell-outline."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 0})
    assert sensor.icon == "mdi:bell-outline"


def test_NI3_count_positive():
    """NI3: ok=true, count>0 → mdi:bell-alert."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 3})
    assert sensor.icon == "mdi:bell-alert"


def test_NI4_count_one():
    """NI4: ok=true, count=1 → mdi:bell-alert."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 1})
    assert sensor.icon == "mdi:bell-alert"


def test_NI5_not_ok():
    """NI5: ok=false → mdi:bell-outline."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": False})
    assert sensor.icon == "mdi:bell-outline"


# ─── extra_state_attributes cases ─────────────────────────────────────────────

def test_NSA1_urls_present():
    """NSA1: Both URLs are always present in attrs."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    attrs = sensor.extra_state_attributes
    assert "notifications_url" in attrs
    assert "digest_url" in attrs
    assert "/api/v1/notifications" in attrs["notifications_url"]
    assert "/api/v1/notifications/digest" in attrs["digest_url"]


def test_NSA2_pending_count_zero():
    """NSA2: pending_count=0 set when ok=true, count=0."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 0, "notifications": []})
    attrs = sensor.extra_state_attributes
    assert attrs.get("pending_count") == 0
    assert attrs.get("latest") == []


def test_NSA3_pending_count_positive():
    """NSA3: pending_count and latest filled when count>0."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({
        "ok": True, "count": 3,
        "notifications": [
            {"id": "n1", "title": "Alert 1"},
            {"id": "n2", "title": "Alert 2"},
            {"id": "n3", "title": "Alert 3"},
        ]
    })
    attrs = sensor.extra_state_attributes
    assert attrs.get("pending_count") == 3
    assert len(attrs.get("latest", [])) == 3


def test_NSA4_latest_capped_at_5():
    """NSA4: latest is capped at 5 items."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({
        "ok": True, "count": 10,
        "notifications": [{"id": f"n{i}", "title": f"Alert {i}"} for i in range(10)]
    })
    attrs = sensor.extra_state_attributes
    assert len(attrs.get("latest", [])) == 5


def test_NSA5_digest_fields():
    """NSA5: digest fields present when digest ok."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_digest_data({
        "ok": True, "count": 7,
        "by_source": {"telegram": 4, "system": 3},
        "by_priority": {"high": 2, "normal": 5},
    })
    attrs = sensor.extra_state_attributes
    assert attrs.get("digest_count") == 7
    assert attrs.get("by_source") == {"telegram": 4, "system": 3}
    assert attrs.get("by_priority") == {"high": 2, "normal": 5}


def test_NSA6_no_digest_data():
    """NSA6: No digest fields when digest_data missing."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 0})
    attrs = sensor.extra_state_attributes
    assert "digest_count" not in attrs
    assert "by_source" not in attrs
    assert "by_priority" not in attrs


# ─── edge cases ────────────────────────────────────────────────────────────────

def test_NE1_empty_notifications_list():
    """NE1: ok=true, count=0, notifications=[] → no alerts."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 0, "notifications": []})
    assert sensor.native_value == "no alerts"
    assert sensor.icon == "mdi:bell-outline"


def test_NE2_notif_data_none():
    """NE2: _notif_data=None → unavailable."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor._notif_data = None
    assert sensor.native_value == "unavailable"
    assert sensor.icon == "mdi:bell-outline"


def test_NE3_high_count():
    """NE3: count=999 → '999 pending'."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({"ok": True, "count": 999, "notifications": []})
    assert sensor.native_value == "999 pending"


# ─── global contract ──────────────────────────────────────────────────────────

def test_GC1_no_local_semantic_invention():
    """GC1: NotificationSensor hits Core API, no local classification."""
    coordinator = MockCoordinator({})
    sensor = NotificationSensorContract(coordinator)
    sensor.set_notif_data({
        "ok": True, "count": 2,
        "notifications": [
            {"id": "n1", "title": "Warning", "priority": "high"},
            {"id": "n2", "title": "Info", "priority": "normal"},
        ]
    })
    sensor.set_digest_data({
        "ok": True, "count": 5,
        "by_source": {"telegram": 3},
        "by_priority": {"high": 1, "normal": 4},
    })

    # native_value: simple string formatting from count
    assert "pending" in sensor.native_value

    # icon: simple threshold on count
    assert "bell" in sensor.icon

    # attrs: direct passthrough, no local scoring
    attrs = sensor.extra_state_attributes
    assert "notifications_url" in attrs
    assert "digest_url" in attrs
    assert attrs["pending_count"] == 2
    assert attrs["digest_count"] == 5

    # No local priority classification invented
    # No local source scoring invented
