"""Projection Contract Tests for BrainArchitectureSensor, OnboardingSensor, and AnomalyDetectionSensor (HA-46).

All are pure Projection-Shells on Core-truth.
Final batch: completes the pure-projection-sensor coverage sweep.
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


# ── BrainArchitectureSensor contract ───────────────────────────────────────

class BrainArchitectureSensorContract:
    """Mirror of BrainArchitectureSensor.

    Contract: hits /api/v1/hub/brain
    """
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        total = self._data.get("total_regions", 0)
        active = self._data.get("active_regions", 0)
        health = self._data.get("health_score", 0)
        if total == 0:
            return "Nicht initialisiert"
        return f"{active}/{total} aktiv ({health}%)"
    @property
    def extra_state_attributes(self):
        return {
            "total_regions": self._data.get("total_regions", 0),
            "active_regions": self._data.get("active_regions", 0),
            "health_score": self._data.get("health_score", 0),
            "total_neurons": self._data.get("total_neurons", 0),
            "synapse_count": self._data.get("synapse_count", 0),
        }


# ── OnboardingSensor contract ──────────────────────────────────────────────

class OnboardingSensorContract:
    """Mirror of OnboardingSensor.

    Contract: hits /api/v1/onboarding/state
    """
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        if self._data.get("is_complete"):
            return "Abgeschlossen"
        current = self._data.get("current_step", 0)
        total = self._data.get("total_steps", 0)
        if total > 0:
            return f"Schritt {current + 1}/{total}"
        return "Nicht gestartet"
    @property
    def icon(self):
        return "mdi:check-decagram" if self._data.get("is_complete") else "mdi:school"
    @property
    def extra_state_attributes(self):
        steps = self._data.get("steps", [])
        completed = sum(1 for s in steps if s.get("completed"))
        skipped = sum(1 for s in steps if s.get("skipped"))
        return {
            "current_step": self._data.get("current_step", 0),
            "total_steps": self._data.get("total_steps", 0),
            "completed_steps": completed,
            "skipped_steps": skipped,
            "is_complete": self._data.get("is_complete", False),
            "agent_name": self._data.get("agent_name", "Styx"),
        }


# ── AnomalyDetectionSensor contract ─────────────────────────────────────────

class AnomalyDetectionSensorContract:
    """Mirror of AnomalyDetectionSensor.

    Contract: hits /api/v1/hub/anomalies
    """
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def state(self):
        total = self._data.get("total_anomalies", 0)
        critical = self._data.get("critical", 0)
        if critical > 0:
            return f"{critical} Kritisch"
        if total > 0:
            return f"{total} Auffällig"
        return "Normal"
    @property
    def extra_state_attributes(self):
        return {
            "total_anomalies": self._data.get("total_anomalies", 0),
            "critical": self._data.get("critical", 0),
            "warning": self._data.get("warning", 0),
            "health_score": self._data.get("health_score", 100),
        }


# ── Tests: BrainArchitectureSensor ─────────────────────────────────────────

def test_BA1_initialized():
    s = BrainArchitectureSensorContract()
    s.apply({"ok": True, "total_regions": 0})
    assert s.native_value == "Nicht initialisiert"

def test_BA2_active():
    s = BrainArchitectureSensorContract()
    s.apply({"ok": True, "total_regions": 8, "active_regions": 6, "health_score": 75})
    assert s.native_value == "6/8 aktiv (75%)"

def test_BA3_attrs():
    s = BrainArchitectureSensorContract()
    s.apply({"ok": True, "total_regions": 8, "active_regions": 6, "health_score": 75, "total_neurons": 150, "synapse_count": 420})
    attrs = s.extra_state_attributes
    assert attrs["total_regions"] == 8
    assert attrs["active_regions"] == 6
    assert attrs["health_score"] == 75
    assert attrs["total_neurons"] == 150
    assert attrs["synapse_count"] == 420


# ── Tests: OnboardingSensor ────────────────────────────────────────────────

def test_OS1_complete():
    s = OnboardingSensorContract()
    s.apply({"ok": True, "is_complete": True, "steps": [{"completed": True}]})
    assert s.native_value == "Abgeschlossen"
    assert s.icon == "mdi:check-decagram"

def test_OS2_in_progress():
    s = OnboardingSensorContract()
    s.apply({"ok": True, "current_step": 2, "total_steps": 5, "steps": [{"completed": True}, {"completed": True}]})
    assert s.native_value == "Schritt 3/5"

def test_OS3_not_started():
    s = OnboardingSensorContract()
    s.apply({"ok": True, "current_step": 0, "total_steps": 0})
    assert s.native_value == "Nicht gestartet"

def test_OS4_icon_in_progress():
    s = OnboardingSensorContract()
    s.apply({"ok": True, "current_step": 1, "total_steps": 5})
    assert s.icon == "mdi:school"

def test_OS5_attrs():
    s = OnboardingSensorContract()
    s.apply({"ok": True, "current_step": 1, "total_steps": 3, "steps": [{"completed": True}, {"skipped": True}], "is_complete": False, "agent_name": "Styx"})
    attrs = s.extra_state_attributes
    assert attrs["completed_steps"] == 1
    assert attrs["skipped_steps"] == 1


# ── Tests: AnomalyDetectionSensor ─────────────────────────────────────────

def test_AD1_critical():
    s = AnomalyDetectionSensorContract()
    s.apply({"ok": True, "total_anomalies": 5, "critical": 2, "warning": 3, "health_score": 70})
    assert s.state == "2 Kritisch"
    attrs = s.extra_state_attributes
    assert attrs["critical"] == 2
    assert attrs["warning"] == 3

def test_AD2_warning_only():
    s = AnomalyDetectionSensorContract()
    s.apply({"ok": True, "total_anomalies": 3, "critical": 0, "warning": 3})
    assert s.state == "3 Auffällig"

def test_AD3_normal():
    s = AnomalyDetectionSensorContract()
    s.apply({"ok": True, "total_anomalies": 0, "critical": 0, "warning": 0})
    assert s.state == "Normal"

def test_AD4_health_score():
    s = AnomalyDetectionSensorContract()
    s.apply({"ok": True, "total_anomalies": 1, "critical": 0, "warning": 1, "health_score": 92})
    attrs = s.extra_state_attributes
    assert attrs["health_score"] == 92
