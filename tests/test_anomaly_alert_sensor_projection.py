"""Projection contract tests for anomaly_alert sensors.

Verifies AnomalyAlertSensor + AlertHistorySensor are pure Projection-Shells
on coordinator.data — triviale Dict-Lookups, keine lokale Semantik-Invention.
"""
import pytest


# ─── AnomalyAlertSensor contract mirrors ─────────────────────────────────────

class AnomalyAlertSensorContract:
    """Mirror of AnomalyAlertSensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "idle"
        anomaly_status = coordinator_data.get("anomaly_status", {})
        if anomaly_status.get("status") == "active":
            summary = anomaly_status.get("summary", {})
            if summary.get("count", 0) > 0:
                return "active"
            return "healthy"
        return "idle"

    @staticmethod
    def attrs(coordinator_data):
        if not coordinator_data:
            return {}
        anomaly_status = coordinator_data.get("anomaly_status", {})
        return {
            "status": anomaly_status.get("status", "unknown"),
            "features": anomaly_status.get("features", []),
            "last_anomaly": anomaly_status.get("summary", {}).get("last_anomaly"),
            "peak_score": anomaly_status.get("summary", {}).get("peak_score", 0),
            "anomaly_count": anomaly_status.get("summary", {}).get("count", 0),
        }


# ─── AlertHistorySensor contract mirrors ─────────────────────────────────────

class AlertHistorySensorContract:
    """Mirror of AlertHistorySensor native_value + attrs logic."""

    @staticmethod
    def native_value(coordinator_data):
        if not coordinator_data:
            return "0"
        alert_history = coordinator_data.get("alert_history", [])
        return str(len(alert_history))

    @staticmethod
    def attrs(coordinator_data):
        if not coordinator_data:
            return {}
        alert_history = coordinator_data.get("alert_history", [])
        return {
            "alerts": [
                {
                    "timestamp": a.get("timestamp", a.get("detected_at", 0)),
                    "score": a.get("score", 0),
                    "is_anomaly": a.get("is_anomaly", True),
                    "device_id": a.get("device_id", a.get("entity_id", "")),
                    "severity": a.get("severity", "info"),
                    "anomaly_type": a.get("anomaly_type", ""),
                }
                for a in alert_history[-50:]
            ],
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
        """status active but summary missing — count defaults to 0, healthy."""
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


# ─── Global Contract ──────────────────────────────────────────────────────────

class TestGlobalContract:
    """GC1: Global projection contract — no local semantic invention."""

    def test_gc1_no_local_logic(self):
        """Verify both sensors only read coordinator.data, no computation."""
        import inspect
        from custom_components.copilot_ha.sensors.anomaly_alert import (
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
        from custom_components.copilot_ha.sensors.anomaly_alert import (
            AnomalyAlertSensor,
            AlertHistorySensor,
        )
        from homeassistant.helpers.update_coordinator import CoordinatorEntity
        assert issubclass(AnomalyAlertSensor, CoordinatorEntity), \
            "AnomalyAlertSensor must inherit CoordinatorEntity"
        assert issubclass(AlertHistorySensor, CoordinatorEntity), \
            "AlertHistorySensor must inherit CoordinatorEntity"
