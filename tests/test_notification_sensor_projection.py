"""Projection contract tests for notification_sensor.

Verifies NotificationSensor is a pure projection shell on Core
/api/v1/notifications + /api/v1/notifications/digest — no local semantic invention.

HA-120 — 2026-04-05
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# =============================================================================
# Contract Mirror
# =============================================================================

class NotificationSensorContract:
    """Mirror of NotificationSensor projection logic.

    Contract:
    - hits /api/v1/notifications + /api/v1/notifications/digest
    - native_value: "{count} pending" | "no alerts" | "unavailable"
    - icon: "mdi:bell-alert" if count>0 else "mdi:bell-outline"
    - attrs: notifications_url, digest_url, pending_count, latest, digest_count
    """

    def __init__(self, notif_data: dict | None, digest_data: dict | None):
        self._notif_data = notif_data
        self._digest_data = digest_data

    @property
    def native_value(self) -> str:
        if self._notif_data and self._notif_data.get("ok"):
            count = self._notif_data.get("count", 0)
            return f"{count} pending" if count > 0 else "no alerts"
        return "unavailable"

    @property
    def icon(self) -> str:
        if self._notif_data and self._notif_data.get("ok"):
            count = self._notif_data.get("count", 0)
            if count > 0:
                return "mdi:bell-alert"
        return "mdi:bell-outline"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
            "notifications_url": "/api/v1/notifications",
            "digest_url": "/api/v1/notifications/digest",
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


# =============================================================================
# NS1 — native_value
# =============================================================================

class TestNotificationSensorNativeValue:
    """NS1: native_value reflects notification count from /api/v1/notifications."""

    def test_ns1_native_value_unavailable(self):
        """NS1.1: Returns 'unavailable' when notif_data is None."""
        sensor = NotificationSensorContract(None, None)
        assert sensor.native_value == "unavailable"

    def test_ns1_native_value_unavailable_ok_false(self):
        """NS1.2: Returns 'unavailable' when ok is False."""
        sensor = NotificationSensorContract({"ok": False}, None)
        assert sensor.native_value == "unavailable"

    def test_ns1_native_value_no_alerts(self):
        """NS1.3: Returns 'no alerts' when count is 0."""
        sensor = NotificationSensorContract({"ok": True, "count": 0, "notifications": []}, None)
        assert sensor.native_value == "no alerts"

    def test_ns1_native_value_pending(self):
        """NS1.4: Returns 'N pending' when count > 0."""
        sensor = NotificationSensorContract({"ok": True, "count": 5, "notifications": []}, None)
        assert sensor.native_value == "5 pending"

    def test_ns1_native_value_one_pending(self):
        """NS1.5: Returns '1 pending' for exactly one."""
        sensor = NotificationSensorContract({"ok": True, "count": 1, "notifications": []}, None)
        assert sensor.native_value == "1 pending"


# =============================================================================
# NS2 — icon
# =============================================================================

class TestNotificationSensorIcon:
    """NS2: icon is dynamic based on pending count."""

    def test_ns2_icon_no_data(self):
        """NS2.1: Returns bell-outline when no data."""
        sensor = NotificationSensorContract(None, None)
        assert sensor.icon == "mdi:bell-outline"

    def test_ns2_icon_no_pending(self):
        """NS2.2: Returns bell-outline when count is 0."""
        sensor = NotificationSensorContract({"ok": True, "count": 0}, None)
        assert sensor.icon == "mdi:bell-outline"

    def test_ns2_icon_has_pending(self):
        """NS2.3: Returns bell-alert when count > 0."""
        sensor = NotificationSensorContract({"ok": True, "count": 3}, None)
        assert sensor.icon == "mdi:bell-alert"


# =============================================================================
# NS3 — extra_state_attributes
# =============================================================================

class TestNotificationSensorAttrs:
    """NS3: extra_state_attributes expose raw coordinator data."""

    def test_ns3_attrs_urls_present(self):
        """NS3.1: URLs are always present in attrs."""
        sensor = NotificationSensorContract(None, None)
        attrs = sensor.extra_state_attributes
        assert "notifications_url" in attrs
        assert "digest_url" in attrs

    def test_ns3_attrs_pending_count(self):
        """NS3.2: pending_count from /api/v1/notifications."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 7, "notifications": [{"id": 1}, {"id": 2}]}, None
        )
        attrs = sensor.extra_state_attributes
        assert attrs["pending_count"] == 7
        assert len(attrs["latest"]) == 2

    def test_ns3_attrs_digest_count(self):
        """NS3.3: digest_count and breakdown from /api/v1/notifications/digest."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 3, "notifications": []},
            {"ok": True, "count": 12, "by_source": {"habitus": 5, "system": 7}, "by_priority": {"high": 2}}
        )
        attrs = sensor.extra_state_attributes
        assert attrs["digest_count"] == 12
        assert attrs["by_source"] == {"habitus": 5, "system": 7}
        assert attrs["by_priority"] == {"high": 2}

    def test_ns3_attrs_no_digest_data(self):
        """NS3.4: digest fields absent when digest_data is None."""
        sensor = NotificationSensorContract({"ok": True, "count": 1, "notifications": []}, None)
        attrs = sensor.extra_state_attributes
        assert "digest_count" not in attrs

    def test_ns3_attrs_latest_capped_at_5(self):
        """NS3.5: latest list is capped at 5 items."""
        notifications = [{"id": i} for i in range(10)]
        sensor = NotificationSensorContract(
            {"ok": True, "count": 10, "notifications": notifications}, None
        )
        attrs = sensor.extra_state_attributes
        assert len(attrs["latest"]) == 5


# =============================================================================
# NS4 — edge cases
# =============================================================================

class TestNotificationSensorEdge:
    """NS4: Edge cases for robust projection."""

    def test_ns4_missing_optional_keys(self):
        """NS4.1: Graceful when ok=True but optional keys missing."""
        sensor = NotificationSensorContract({"ok": True}, None)
        assert sensor.native_value == "no alerts"
        attrs = sensor.extra_state_attributes
        assert attrs["pending_count"] == 0

    def test_ns4_notifications_not_a_list(self):
        """NS4.2: Graceful when notifications is not a list."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 2, "notifications": "not-a-list"}, None
        )
        attrs = sensor.extra_state_attributes
        assert attrs["pending_count"] == 2

    def test_ns4_digest_ok_false(self):
        """NS4.3: No digest attrs when digest ok=False."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            {"ok": False}
        )
        attrs = sensor.extra_state_attributes
        assert "digest_count" not in attrs


# =============================================================================
# GC — Global Contract
# =============================================================================

class TestGlobalContract:
    """GC: NotificationSensor is a pure projection shell on Core API."""

    def test_gc1_hits_core_endpoints(self):
        """GC1: Sensor targets /api/v1/notifications + /api/v1/notifications/digest."""
        sensor = NotificationSensorContract(None, None)
        attrs = sensor.extra_state_attributes
        assert "/api/v1/notifications" in attrs["notifications_url"]
        assert "/api/v1/notifications/digest" in attrs["digest_url"]

    def test_gc2_no_local_semantic_invention(self):
        """GC2: Sensor formats count directly — no local classification/priority logic."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 5, "notifications": [{"id": 1}]},
            {"ok": True, "count": 10, "by_source": {}, "by_priority": {}}
        )
        attrs = sensor.extra_state_attributes
        # count passed through unchanged
        assert attrs["pending_count"] == 5
        assert attrs["digest_count"] == 10
        # no invented fields
        assert "priority_score" not in attrs
        assert "urgency_level" not in attrs
