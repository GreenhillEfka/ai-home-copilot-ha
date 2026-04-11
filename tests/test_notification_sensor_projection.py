"""Projection contract tests for notification_sensor.

Verifies NotificationSensor is a pure projection shell on Core
/api/v1/notifications + /api/v1/notifications/digest — no local semantic invention.

Contract: sensor derives ALL display values from Core API payloads via trivial
Dict-lookups and string formatting. No local classification, no heuristic.

Malformed-payload guards added: NSM1–NSM10, NSGC1–NSGC3 (HA-337)

HA-120 — 2026-04-05
HA-337 — 2026-04-11
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# =============================================================================
# Contract Mirror
# =============================================================================

def _as_mapping(val):
    if isinstance(val, dict):
        return val
    return {}


def _as_list(val):
    if isinstance(val, list):
        return val
    return []


def _safe_count(val):
    if isinstance(val, int) and not isinstance(val, bool) and val >= 0:
        return val
    return 0


def _is_ok(data):
    return data.get("ok") is True


class NotificationSensorContract:
    """Mirror of NotificationSensor projection logic with guard semantics."""

    def __init__(self, notif_data, digest_data):
        self._notif_data = notif_data
        self._digest_data = digest_data

    @property
    def native_value(self) -> str:
        notif = _as_mapping(self._notif_data)
        if not notif or not _is_ok(notif):
            return "unavailable"
        count = _safe_count(notif.get("count"))
        return f"{count} pending" if count > 0 else "no alerts"

    @property
    def icon(self) -> str:
        notif = _as_mapping(self._notif_data)
        if not notif or not _is_ok(notif):
            return "mdi:bell-outline"
        count = _safe_count(notif.get("count"))
        return "mdi:bell-alert" if count > 0 else "mdi:bell-outline"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {
            "notifications_url": "/api/v1/notifications",
            "digest_url": "/api/v1/notifications/digest",
        }
        notif = _as_mapping(self._notif_data)
        if notif and _is_ok(notif):
            notifications = _as_list(notif.get("notifications"))
            count = _safe_count(notif.get("count"))
            attrs["pending_count"] = count
            attrs["latest"] = notifications[:5]
        digest = _as_mapping(self._digest_data)
        if digest and _is_ok(digest):
            attrs["digest_count"] = _safe_count(digest.get("count"))
            attrs["by_source"] = _as_mapping(digest.get("by_source"))
            attrs["by_priority"] = _as_mapping(digest.get("by_priority"))
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
# NSM — Malformed payload guards (HA-337)
# =============================================================================

class TestNotificationSensorMalformed:
    """NSM: Guard against malformed Core API payloads."""

    # --- Top-level non-dict payloads ---

    def test_nsm1_notif_top_level_string(self):
        """NSM1: String top-level → 'unavailable'."""
        sensor = NotificationSensorContract("not-a-dict", None)
        assert sensor.native_value == "unavailable"
        assert sensor.icon == "mdi:bell-outline"

    def test_nsm2_notif_top_level_list(self):
        """NSM2: List top-level → 'unavailable'."""
        sensor = NotificationSensorContract([{"ok": True}], None)
        assert sensor.native_value == "unavailable"

    def test_nsm3_notif_top_level_int(self):
        """NSM3: Integer top-level → 'unavailable'."""
        sensor = NotificationSensorContract(42, None)
        assert sensor.native_value == "unavailable"

    def test_nsm4_notif_top_level_none(self):
        """NSM4: None top-level → 'unavailable' (unchanged behavior)."""
        sensor = NotificationSensorContract(None, None)
        assert sensor.native_value == "unavailable"

    # --- ok field edge cases ---

    def test_nsm5_ok_is_none(self):
        """NSM5: ok=None treated as unavailable."""
        sensor = NotificationSensorContract({"ok": None, "count": 5}, None)
        assert sensor.native_value == "unavailable"

    def test_nsm6_ok_is_string(self):
        """NSM6: ok='true' (string) → unavailable."""
        sensor = NotificationSensorContract({"ok": "true", "count": 5}, None)
        assert sensor.native_value == "unavailable"

    def test_nsm7_ok_is_int(self):
        """NSM7: ok=1 (int) → unavailable (needs strict True)."""
        sensor = NotificationSensorContract({"ok": 1, "count": 5}, None)
        assert sensor.native_value == "unavailable"

    # --- count field malformed ---

    def test_nsm8_count_string(self):
        """NSM8: count='5' (string) → 0, 'no alerts'."""
        sensor = NotificationSensorContract({"ok": True, "count": "5"}, None)
        assert sensor.native_value == "no alerts"

    def test_nsm9_count_negative(self):
        """NSM9: count=-3 → 0, 'no alerts'."""
        sensor = NotificationSensorContract({"ok": True, "count": -3}, None)
        assert sensor.native_value == "no alerts"

    def test_nsm10_count_float(self):
        """NSM10: count=3.14 (float) → 0, 'no alerts'."""
        sensor = NotificationSensorContract({"ok": True, "count": 3.14}, None)
        assert sensor.native_value == "no alerts"

    def test_nsm11_count_bool_true(self):
        """NSM11: count=True (bool) → 0, 'no alerts'."""
        sensor = NotificationSensorContract({"ok": True, "count": True}, None)
        assert sensor.native_value == "no alerts"

    def test_nsm12_count_none(self):
        """NSM12: count=None → 0, 'no alerts'."""
        sensor = NotificationSensorContract({"ok": True, "count": None}, None)
        assert sensor.native_value == "no alerts"

    # --- notifications malformed ---

    def test_nsm13_notifications_dict(self):
        """NSM13: notifications={} (dict, not list) → latest=[]."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": {"a": 1}}, None
        )
        attrs = sensor.extra_state_attributes
        assert attrs["latest"] == []

    def test_nsm14_notifications_string(self):
        """NSM14: notifications='abc' (string) → latest=[]."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": "abc"}, None
        )
        attrs = sensor.extra_state_attributes
        assert attrs["latest"] == []

    def test_nsm15_notifications_int(self):
        """NSM15: notifications=42 (int) → latest=[]."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": 42}, None
        )
        attrs = sensor.extra_state_attributes
        assert attrs["latest"] == []

    # --- digest malformed ---

    def test_nsm16_digest_top_level_string(self):
        """NSM16: digest string → no digest attrs."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            "not-a-dict"
        )
        attrs = sensor.extra_state_attributes
        assert "digest_count" not in attrs

    def test_nsm17_digest_ok_none(self):
        """NSM17: digest ok=None → no digest attrs."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            {"ok": None, "count": 5}
        )
        attrs = sensor.extra_state_attributes
        assert "digest_count" not in attrs

    def test_nsm18_digest_count_string(self):
        """NSM18: digest count='7' (string) → digest_count=0."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            {"ok": True, "count": "7"}
        )
        attrs = sensor.extra_state_attributes
        assert attrs["digest_count"] == 0

    def test_nsm19_digest_by_source_string(self):
        """NSM19: digest by_source='bad' (string) → {}."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            {"ok": True, "count": 3, "by_source": "bad"}
        )
        attrs = sensor.extra_state_attributes
        assert attrs["by_source"] == {}

    def test_nsm20_digest_by_priority_list(self):
        """NSM20: digest by_priority=[1,2] (list) → {}."""
        sensor = NotificationSensorContract(
            {"ok": True, "count": 1, "notifications": []},
            {"ok": True, "count": 3, "by_priority": [1, 2]}
        )
        attrs = sensor.extra_state_attributes
        assert attrs["by_priority"] == {}


# =============================================================================
# NSGC — Source guards (HA-337)
# =============================================================================

class TestNotificationSensorSourceGuard:
    """NSGC: Guard helpers are anchored in the production module."""

    def test_nsgc1_as_mapping_defined(self):
        """NSGC1: _as_mapping exists and rejects non-dict."""
        from custom_components.pilotsuite.sensors.notification_sensor import _as_mapping
        assert _as_mapping({"a": 1}) == {"a": 1}
        assert _as_mapping("string") == {}
        assert _as_mapping(None) == {}
        assert _as_mapping([1, 2]) == {}

    def test_nsgc2_as_list_defined(self):
        """NSGC2: _as_list exists and rejects non-list."""
        from custom_components.pilotsuite.sensors.notification_sensor import _as_list
        assert _as_list([1, 2]) == [1, 2]
        assert _as_list("string") == []
        assert _as_list(None) == []
        assert _as_list({"a": 1}) == []

    def test_nsgc3_safe_count_defined(self):
        """NSGC3: _safe_count exists and enforces int >= 0."""
        from custom_components.pilotsuite.sensors.notification_sensor import _safe_count
        assert _safe_count(5) == 5
        assert _safe_count(0) == 0
        assert _safe_count("5") == 0
        assert _safe_count(-3) == 0
        assert _safe_count(3.14) == 0
        assert _safe_count(True) == 0
        assert _safe_count(None) == 0
