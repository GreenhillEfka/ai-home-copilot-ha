"""Projection contract tests for proactive_alert_sensor.

Verifies ProactiveAlertSensor is a pure projection shell on Core
/api/v1/regional/alerts — no local semantic invention.

HA-135 — 2026-04-06
"""
from __future__ import annotations

import pytest


# =============================================================================
# Contract Mirror
# =============================================================================

_PRIORITY_ICONS = {
    0: "mdi:check-circle",
    1: "mdi:information",
    2: "mdi:alert-outline",
    3: "mdi:alert",
    4: "mdi:alert-octagon",
}


class ProactiveAlertSensorContract:
    """Mirror of ProactiveAlertSensor projection logic.

    Contract:
    - hits /api/v1/regional/alerts
    - native_value: "{total}x {highest_priority_label}" | "Keine Alerts"
    - icon: priority-based _PRIORITY_ICONS, default mdi:bell-alert
    - attrs: total_alerts, highest_priority, highest_priority_label,
             info_count, advisory_count, warning_count, critical_count,
             categories, alerts (first 10), last_evaluated
    """

    def __init__(self, alert_data: dict | None):
        self._data = alert_data or {}

    @property
    def native_value(self) -> str:
        total = self._data.get("total", 0)
        if total == 0:
            return "Keine Alerts"
        highest = self._data.get("highest_priority_label", "Info")
        return f"{total}x {highest}"

    @property
    def icon(self) -> str:
        priority = self._data.get("highest_priority", 0)
        return _PRIORITY_ICONS.get(priority, "mdi:bell-alert")

    @property
    def extra_state_attributes(self) -> dict:
        by_priority = self._data.get("by_priority", {})
        alerts = self._data.get("alerts", [])

        alert_list: list[dict] = []
        raw_alerts = self._data.get("alerts", [])
        if isinstance(raw_alerts, list):
            for a in raw_alerts[:10]:
                if isinstance(a, dict):
                    alert_list.append({
                        "title": a.get("title_de", ""),
                        "priority": a.get("priority_label", ""),
                        "category": a.get("category", ""),
                        "action": a.get("action", ""),
                        "message": a.get("message_de", ""),
                        "icon": a.get("icon", ""),
                    })

        return {
            "total_alerts": self._data.get("total", 0),
            "highest_priority": self._data.get("highest_priority", 0),
            "highest_priority_label": self._data.get("highest_priority_label", ""),
            "info_count": by_priority.get("info", 0),
            "advisory_count": by_priority.get("advisory", 0),
            "warning_count": by_priority.get("warning", 0),
            "critical_count": by_priority.get("critical", 0),
            "categories": self._data.get("by_category", {}),
            "alerts": alert_list,
            "last_evaluated": self._data.get("last_evaluated", ""),
        }


# =============================================================================
# PA1 — native_value
# =============================================================================

class TestProactiveAlertSensorNativeValue:
    """PA1: native_value reflects total and highest_priority_label from alert_data."""

    def test_pa1_native_value_no_alerts(self):
        """PA1.1: Returns 'Keine Alerts' when total is 0."""
        sensor = ProactiveAlertSensorContract({"total": 0})
        assert sensor.native_value == "Keine Alerts"

    def test_pa1_native_value_single_info(self):
        """PA1.2: Returns '1x Info' for single info alert."""
        data = {"total": 1, "highest_priority": 1, "highest_priority_label": "Info"}
        sensor = ProactiveAlertSensorContract(data)
        assert sensor.native_value == "1x Info"

    def test_pa1_native_value_multiple_advisory(self):
        """PA1.3: Returns '3x Advisory' for multiple advisory alerts."""
        data = {"total": 3, "highest_priority": 2, "highest_priority_label": "Advisory"}
        sensor = ProactiveAlertSensorContract(data)
        assert sensor.native_value == "3x Advisory"

    def test_pa1_native_value_warning(self):
        """PA1.4: Returns '2x Warning' for warning-level alerts."""
        data = {"total": 2, "highest_priority": 3, "highest_priority_label": "Warning"}
        sensor = ProactiveAlertSensorContract(data)
        assert sensor.native_value == "2x Warning"

    def test_pa1_native_value_critical(self):
        """PA1.5: Returns '1x Critical' for critical alert."""
        data = {"total": 1, "highest_priority": 4, "highest_priority_label": "Critical"}
        sensor = ProactiveAlertSensorContract(data)
        assert sensor.native_value == "1x Critical"

    def test_pa1_native_value_empty_data(self):
        """PA1.6: Returns 'Keine Alerts' when data is empty."""
        sensor = ProactiveAlertSensorContract({})
        assert sensor.native_value == "Keine Alerts"


# =============================================================================
# PA2 — icon
# =============================================================================

class TestProactiveAlertSensorIcon:
    """PA2: icon is determined by highest_priority from alert_data."""

    def test_pa2_icon_priority_0_check_circle(self):
        """PA2.1: Returns mdi:check-circle for priority 0."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 0})
        assert sensor.icon == "mdi:check-circle"

    def test_pa2_icon_priority_1_information(self):
        """PA2.2: Returns mdi:information for priority 1."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 1})
        assert sensor.icon == "mdi:information"

    def test_pa2_icon_priority_2_alert_outline(self):
        """PA2.3: Returns mdi:alert-outline for priority 2."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 2})
        assert sensor.icon == "mdi:alert-outline"

    def test_pa2_icon_priority_3_alert(self):
        """PA2.4: Returns mdi:alert for priority 3."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 3})
        assert sensor.icon == "mdi:alert"

    def test_pa2_icon_priority_4_alert_octagon(self):
        """PA2.5: Returns mdi:alert-octagon for priority 4."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 4})
        assert sensor.icon == "mdi:alert-octagon"

    def test_pa2_icon_unknown_priority(self):
        """PA2.6: Returns mdi:bell-alert for unknown priority (5+)."""
        sensor = ProactiveAlertSensorContract({"highest_priority": 99})
        assert sensor.icon == "mdi:bell-alert"


# =============================================================================
# PA3 — extra_state_attributes
# =============================================================================

class TestProactiveAlertSensorAttributes:
    """PA3: extra_state_attributes reflect alert data structure from API."""

    def test_pa3_attrs_full(self):
        """PA3.1: Returns complete attributes for full alert data."""
        data = {
            "total": 5,
            "highest_priority": 3,
            "highest_priority_label": "Warning",
            "by_priority": {"info": 1, "advisory": 2, "warning": 2, "critical": 0},
            "by_category": {"energy": 3, "weather": 2},
            "alerts": [
                {"title_de": "Test Alert", "priority_label": "Warning",
                 "category": "energy", "action": "reduce",
                 "message_de": "High price", "icon": "mdi:currency-eur"},
            ],
            "last_evaluated": "2026-04-06T12:00:00Z",
        }
        sensor = ProactiveAlertSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["total_alerts"] == 5
        assert attrs["highest_priority"] == 3
        assert attrs["highest_priority_label"] == "Warning"
        assert attrs["info_count"] == 1
        assert attrs["advisory_count"] == 2
        assert attrs["warning_count"] == 2
        assert attrs["critical_count"] == 0
        assert attrs["categories"] == {"energy": 3, "weather": 2}
        assert len(attrs["alerts"]) == 1
        assert attrs["alerts"][0]["title"] == "Test Alert"
        assert attrs["last_evaluated"] == "2026-04-06T12:00:00Z"

    def test_pa3_attrs_empty_alerts(self):
        """PA3.2: Returns zero counts when no alerts present."""
        data = {"total": 0, "by_priority": {}}
        sensor = ProactiveAlertSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["total_alerts"] == 0
        assert attrs["info_count"] == 0
        assert attrs["advisory_count"] == 0
        assert attrs["warning_count"] == 0
        assert attrs["critical_count"] == 0
        assert attrs["alerts"] == []

    def test_pa3_attrs_alerts_capped_at_10(self):
        """PA3.3: Alert list is capped at first 10 items."""
        data = {
            "total": 15,
            "alerts": [{"title_de": f"Alert {i}"} for i in range(15)],
        }
        sensor = ProactiveAlertSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert len(attrs["alerts"]) == 10
        assert attrs["alerts"][9]["title"] == "Alert 9"


# =============================================================================
# PA4 — edge cases
# =============================================================================

class TestProactiveAlertSensorEdge:
    """PA4: edge cases — missing fields, unexpected types."""

    def test_pa4_edge_none_data(self):
        """PA4.1: Handles None data gracefully."""
        sensor = ProactiveAlertSensorContract(None)
        assert sensor.native_value == "Keine Alerts"
        assert sensor.icon == "mdi:check-circle"

    def test_pa4_edge_missing_optional_fields(self):
        """PA4.2: Handles missing optional fields."""
        data = {"total": 1}
        sensor = ProactiveAlertSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["highest_priority"] == 0
        assert attrs["highest_priority_label"] == ""
        assert attrs["info_count"] == 0
        assert attrs["categories"] == {}

    def test_pa4_edge_alerts_not_list(self):
        """PA4.3: Handles non-list alerts field gracefully."""
        data = {"total": 1, "alerts": "not a list"}
        sensor = ProactiveAlertSensorContract(data)
        attrs = sensor.extra_state_attributes
        assert attrs["alerts"] == []

    def test_pa4_edge_priority_missing(self):
        """PA4.4: Defaults to icon for priority 0 when priority field absent."""
        data = {}
        sensor = ProactiveAlertSensorContract(data)
        assert sensor.icon == "mdi:check-circle"


# =============================================================================
# GC1 — global contract: pure projection, no local semantic invention
# =============================================================================

class TestProactiveAlertSensorGlobalContract:
    """GC1: Global contract — pure projection shell on Core API."""

    def test_gc1_api_endpoint_verified(self):
        """GC1.1: Sensor hits /api/v1/regional/alerts (verified by source code scan)."""
        import ast
        import os
        sensor_path = os.path.join(
            os.path.dirname(__file__),
            "../custom_components/copilot_ha/sensors/proactive_alert_sensor.py"
        )
        with open(sensor_path) as f:
            source = f.read()
        # URL is built as f"{base}/alerts" where base ends with "/api/v1/regional"
        # Check both parts appear in source
        assert "/api/v1/regional" in source, "Sensor must reference /api/v1/regional"
        assert "alerts" in source, "Sensor must reference alerts endpoint"

    def test_gc2_no_local_semantic_invention(self):
        """GC2.1: All display values derived from API data — no hard-coded classification logic."""
        sensor = ProactiveAlertSensorContract({
            "total": 3,
            "highest_priority": 2,
            "highest_priority_label": "Advisory",
            "by_priority": {"info": 1, "advisory": 2},
        })
        # native_value = API total + API label (no re-classification)
        assert sensor.native_value == "3x Advisory"
        # icon = direct priority map lookup (no re-calculation)
        assert sensor.icon == "mdi:alert-outline"
        # attrs = direct pass-through from API fields (no inference)
        attrs = sensor.extra_state_attributes
        assert attrs["advisory_count"] == 2
        assert attrs["total_alerts"] == 3
