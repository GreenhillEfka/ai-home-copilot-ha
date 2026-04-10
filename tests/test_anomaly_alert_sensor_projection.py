"""Projection contract tests for anomaly_alert sensors.

Verifies AnomalyAlertSensor + AlertHistorySensor are pure Projection-Shells
on coordinator.data — triviale Dict-Lookups, keine lokale Semantik-Invention.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# =============================================================================
# Guard helpers — mirror of production code
# =============================================================================

def _as_mapping(val):
    if isinstance(val, dict):
        return val
    return {}


def _as_list(val):
    if isinstance(val, list):
        return val
    return []


def _guard_item(a):
    if not isinstance(a, dict):
        return {
            "timestamp": 0,
            "score": 0,
            "is_anomaly": True,
            "device_id": "",
            "severity": "info",
            "anomaly_type": "",
        }
    ts = a.get("timestamp") if a.get("timestamp") is not None else a.get("detected_at", 0)
    return {
        "timestamp": ts if isinstance(ts, (int, float)) else 0,
        "score": a.get("score", 0) if isinstance(a.get("score"), (int, float)) else 0,
        "is_anomaly": bool(a.get("is_anomaly")) if a.get("is_anomaly") is not None else True,
        "device_id": a.get("device_id", a.get("entity_id", "")) if isinstance(a.get("device_id", a.get("entity_id", "")), str) else "",
        "severity": a.get("severity", "info") if isinstance(a.get("severity", "info"), str) else "info",
        "anomaly_type": a.get("anomaly_type", "") if isinstance(a.get("anomaly_type", ""), str) else "",
    }


# ─── AnomalyAlertSensor contract mirrors ─────────────────────────────────────

class AnomalyAlertSensorContract:
    """Mirror of AnomalyAlertSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return "idle"
        anomaly_status = _as_mapping(data.get("anomaly_status", {}))
        status = anomaly_status.get("status")
        if status == "active":
            summary = _as_mapping(anomaly_status.get("summary", {}))
            count = summary.get("count", 0)
            if isinstance(count, (int, float)) and count > 0:
                return "active"
            return "healthy"
        return "idle"

    @staticmethod
    def attrs(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return {}
        anomaly_status = _as_mapping(data.get("anomaly_status", {}))
        summary = _as_mapping(anomaly_status.get("summary", {}))
        features_raw = anomaly_status.get("features")
        features = _as_list(features_raw) if features_raw is not None else []
        return {
            "status": anomaly_status.get("status", "unknown"),
            "features": features,
            "last_anomaly": summary.get("last_anomaly"),
            "peak_score": summary.get("peak_score", 0),
            "anomaly_count": summary.get("count", 0),
        }


# ─── AlertHistorySensor contract mirrors ─────────────────────────────────────

class AlertHistorySensorContract:
    """Mirror of AlertHistorySensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return "0"
        alert_history = _as_list(data.get("alert_history", []))
        return str(len(alert_history))

    @staticmethod
    def attrs(coordinator_data):
        data = _as_mapping(coordinator_data)
        if not data:
            return {}
        alert_history = _as_list(data.get("alert_history", []))
        return {
            "alerts": [_guard_item(a) for a in alert_history[-50:]],
            "count": len(alert_history),
            "recent_anomalies": len(alert_history),
        }


# ─── AnomalyAlertSensor Tests ────────────────────────────────────────────────

class TestAAXNativeValue:
    """AA1: native_value cases for AnomalyAlertSensor."""

    def test_aa1_active_with_count(self):
        """Active anomaly detected — count > 0."""
        data = {
            "anomaly_status": {
                "status": "active",
                "summary": {"count": 3, "last_anomaly": 12345, "peak_score": 0.92}
            }
        }
        assert AnomalyAlertSensorContract.native_value(data) == "active"

    def test_aa2_active_no_count(self):
        """Active status but count == 0 — healthy."""
        data = {
            "anomaly_status": {
                "status": "active",
                "summary": {"count": 0}
            }
        }
        assert AnomalyAlertSensorContract.native_value(data) == "healthy"

    def test_aa3_not_active(self):
        """Status not 'active' — idle."""
        data = {
            "anomaly_status": {
                "status": "inactive",
                "summary": {"count": 0}
            }
        }
        assert AnomalyAlertSensorContract.native_value(data) == "idle"

    def test_aa4_no_data(self):
        """Empty coordinator data — idle."""
        assert AnomalyAlertSensorContract.native_value(None) == "idle"

    def test_aa5_empty_anomaly_status(self):
        """Empty anomaly_status dict — idle."""
        assert AnomalyAlertSensorContract.native_value({"anomaly_status": {}}) == "idle"

    def test_aa6_missing_summary(self):
        """status active but summary missing — healthy."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": {"status": "active"}}
        ) == "healthy"


class TestAAXAttrs:
    """AA2: extra_state_attributes for AnomalyAlertSensor."""

    def test_aa7_full_attrs(self):
        """Full anomaly_status with all fields."""
        data = {
            "anomaly_status": {
                "status": "active",
                "features": ["temperature", "humidity"],
                "summary": {
                    "last_anomaly": 99999,
                    "peak_score": 0.87,
                    "count": 5
                }
            }
        }
        attrs = AnomalyAlertSensorContract.attrs(data)
        assert attrs["status"] == "active"
        assert attrs["features"] == ["temperature", "humidity"]
        assert attrs["last_anomaly"] == 99999
        assert attrs["peak_score"] == 0.87
        assert attrs["anomaly_count"] == 5

    def test_aa8_empty_attrs(self):
        """Empty coordinator data — empty dict."""
        assert AnomalyAlertSensorContract.attrs(None) == {}

    def test_aa9_defaults(self):
        """Missing optional fields — defaults applied."""
        attrs = AnomalyAlertSensorContract.attrs(
            {"anomaly_status": {"status": "unknown"}}
        )
        assert attrs["status"] == "unknown"
        assert attrs["features"] == []
        assert attrs["peak_score"] == 0
        assert attrs["anomaly_count"] == 0


# ─── AlertHistorySensor Tests ────────────────────────────────────────────────

class TestAHXNativeValue:
    """AH1: native_value cases for AlertHistorySensor."""

    def test_ah1_with_alerts(self):
        """Alert history with 3 entries — '3'."""
        data = {
            "alert_history": [
                {"timestamp": 100, "score": 0.5},
                {"timestamp": 200, "score": 0.7},
                {"timestamp": 300, "score": 0.9},
            ]
        }
        assert AlertHistorySensorContract.native_value(data) == "3"

    def test_ah2_empty(self):
        """Empty alert_history — '0'."""
        assert AlertHistorySensorContract.native_value(
            {"alert_history": []}
        ) == "0"

    def test_ah3_no_key(self):
        """No alert_history key — '0'."""
        assert AlertHistorySensorContract.native_value({}) == "0"

    def test_ah4_none(self):
        """None data — '0'."""
        assert AlertHistorySensorContract.native_value(None) == "0"


class TestAHXAttrs:
    """AH2: extra_state_attributes for AlertHistorySensor."""

    def test_ah5_full_attrs(self):
        """Full alert_history with 2 entries."""
        data = {
            "alert_history": [
                {
                    "timestamp": 100,
                    "score": 0.85,
                    "is_anomaly": True,
                    "device_id": "sensor.temperature_1",
                    "severity": "high",
                    "anomaly_type": "spike"
                },
                {
                    "detected_at": 200,
                    "score": 0.72,
                    "is_anomaly": False,
                    "entity_id": "sensor.humidity_1",
                    "severity": "low",
                    "anomaly_type": "drift"
                }
            ]
        }
        attrs = AlertHistorySensorContract.attrs(data)
        assert attrs["count"] == 2
        assert attrs["recent_anomalies"] == 2
        assert len(attrs["alerts"]) == 2
        # first alert uses timestamp
        assert attrs["alerts"][0]["timestamp"] == 100
        assert attrs["alerts"][0]["score"] == 0.85
        assert attrs["alerts"][0]["device_id"] == "sensor.temperature_1"
        # second uses detected_at fallback
        assert attrs["alerts"][1]["timestamp"] == 200
        assert attrs["alerts"][1]["device_id"] == "sensor.humidity_1"

    def test_ah6_empty(self):
        """Empty coordinator data — empty dict."""
        assert AlertHistorySensorContract.attrs(None) == {}

    def test_ah7_empty_history(self):
        """Empty alert_history list."""
        attrs = AlertHistorySensorContract.attrs({"alert_history": []})
        assert attrs["alerts"] == []
        assert attrs["count"] == 0

    def test_ah8_capped_at_50(self):
        """Alert list capped at 50 entries."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": i, "score": 0.5} for i in range(100)]}
        )
        assert len(attrs["alerts"]) == 50
        assert attrs["count"] == 100

    def test_ah9_defaults(self):
        """Missing optional fields in alert entries — defaults."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": 42}]}
        )
        alert = attrs["alerts"][0]
        assert alert["score"] == 0
        assert alert["is_anomaly"] is True
        assert alert["device_id"] == ""
        assert alert["severity"] == "info"
        assert alert["anomaly_type"] == ""


# ─── Malformed Payload Cases ─────────────────────────────────────────────────

class TestAAMalformed:
    """AAM: AnomalyAlertSensor malformed payload guard cases."""

    def test_aam1_anomaly_status_string(self):
        """anomaly_status is a string — treated as empty dict, idle."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": "not_a_dict"}
        ) == "idle"

    def test_aam2_anomaly_status_list(self):
        """anomaly_status is a list — treated as empty dict, idle."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": ["active", "summary"]}
        ) == "idle"

    def test_aam3_anomaly_status_none(self):
        """anomaly_status is None — idle."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": None}
        ) == "idle"

    def test_aam4_summary_string(self):
        """summary is a string — treated as empty dict, healthy."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": {"status": "active", "summary": "bad"}}
        ) == "healthy"

    def test_aam5_summary_list(self):
        """summary is a list — treated as empty dict, healthy."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": {"status": "active", "summary": [1, 2, 3]}}
        ) == "healthy"

    def test_aam6_count_string(self):
        """count is a string — not > 0, healthy."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": {"status": "active", "summary": {"count": "5"}}}
        ) == "healthy"

    def test_aam7_count_none(self):
        """count is None — healthy."""
        assert AnomalyAlertSensorContract.native_value(
            {"anomaly_status": {"status": "active", "summary": {"count": None}}}
        ) == "healthy"

    def test_aam8_features_string(self):
        """features is a string — attrs uses empty list."""
        attrs = AnomalyAlertSensorContract.attrs(
            {"anomaly_status": {"status": "active", "features": "temperature"}}
        )
        assert attrs["features"] == []

    def test_aam9_features_dict(self):
        """features is a dict — attrs uses empty list."""
        attrs = AnomalyAlertSensorContract.attrs(
            {"anomaly_status": {"status": "active", "features": {"temp": 1}}}
        )
        assert attrs["features"] == []

    def test_aam10_attrs_anomaly_status_string(self):
        """anomaly_status string in attrs — safe defaults."""
        attrs = AnomalyAlertSensorContract.attrs({"anomaly_status": "broken"})
        assert attrs["status"] == "unknown"
        assert attrs["features"] == []
        assert attrs["peak_score"] == 0
        assert attrs["anomaly_count"] == 0


class TestAHMalformed:
    """AHM: AlertHistorySensor malformed payload guard cases."""

    def test_ahm1_alert_history_string(self):
        """alert_history is a string — empty list, '0'."""
        assert AlertHistorySensorContract.native_value(
            {"alert_history": "not_a_list"}
        ) == "0"

    def test_ahm2_alert_history_dict(self):
        """alert_history is a dict — empty list, '0'."""
        assert AlertHistorySensorContract.native_value(
            {"alert_history": {"key": "value"}}
        ) == "0"

    def test_ahm3_alert_history_int(self):
        """alert_history is an int — empty list, '0'."""
        assert AlertHistorySensorContract.native_value(
            {"alert_history": 42}
        ) == "0"

    def test_ahm4_alert_entry_non_dict(self):
        """Alert list entry is a string — guarded to safe defaults."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": ["not_a_dict_item"]}
        )
        assert attrs["count"] == 1
        assert attrs["alerts"][0]["timestamp"] == 0
        assert attrs["alerts"][0]["score"] == 0
        assert attrs["alerts"][0]["device_id"] == ""

    def test_ahm5_alert_entry_none(self):
        """Alert list entry is None — guarded to safe defaults."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [None]}
        )
        assert attrs["alerts"][0]["timestamp"] == 0
        assert attrs["alerts"][0]["score"] == 0
        assert attrs["alerts"][0]["is_anomaly"] is True

    def test_ahm6_timestamp_string(self):
        """timestamp is a string — guarded to 0."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": "now", "score": 0.5}]}
        )
        assert attrs["alerts"][0]["timestamp"] == 0

    def test_ahm7_score_string(self):
        """score is a string — guarded to 0."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": 100, "score": "high"}]}
        )
        assert attrs["alerts"][0]["score"] == 0

    def test_ahm8_is_anomaly_string(self):
        """is_anomaly is a string — guarded to True."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": 100, "is_anomaly": "yes"}]}
        )
        assert attrs["alerts"][0]["is_anomaly"] is True

    def test_ahm9_device_id_int(self):
        """device_id is an int — guarded to empty string."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": 100, "device_id": 12345}]}
        )
        assert attrs["alerts"][0]["device_id"] == ""

    def test_ahm10_severity_int(self):
        """severity is an int — guarded to 'info'."""
        attrs = AlertHistorySensorContract.attrs(
            {"alert_history": [{"timestamp": 100, "severity": 9}]}
        )
        assert attrs["alerts"][0]["severity"] == "info"


# ─── Global Contract ──────────────────────────────────────────────────────────

class TestGlobalContract:
    """GC1: Global projection contract — no local semantic invention."""

    def test_gc1_no_local_logic(self):
        """Verify both sensors only read coordinator.data, no computation."""
        import inspect
        from custom_components.pilotsuite.sensors.anomaly_alert import (
            AnomalyAlertSensor,
            AlertHistorySensor,
        )

        for cls in [AnomalyAlertSensor, AlertHistorySensor]:
            source = inspect.getsource(cls)
            # No Math/logic beyond dict .get() and len()
            assert "min(" not in source and "max(" not in source, \
                f"{cls.__name__} contains forbidden logic"
            assert "round(" not in source
            # Only simple if-get patterns allowed
            assert "self.coordinator.data" in source, \
                f"{cls.__name__} must read coordinator.data"

    def test_gc2_coordinator_entity_pattern(self):
        """Both sensors use CoordinatorEntity inheritance."""
        from custom_components.pilotsuite.sensors.anomaly_alert import (
            AnomalyAlertSensor,
            AlertHistorySensor,
        )
        from homeassistant.helpers.update_coordinator import CoordinatorEntity
        assert issubclass(AnomalyAlertSensor, CoordinatorEntity), \
            "AnomalyAlertSensor must inherit CoordinatorEntity"
        assert issubclass(AlertHistorySensor, CoordinatorEntity), \
            "AlertHistorySensor must inherit CoordinatorEntity"

    def test_gc3_source_guards(self):
        """Guard helpers are defined and used in production module."""
        import inspect
        from custom_components.pilotsuite.sensors import anomaly_alert as module
        source = inspect.getsource(module)
        assert "_as_mapping" in source, "anomaly_alert must define _as_mapping"
        assert "_as_list" in source, "anomaly_alert must define _as_list"
