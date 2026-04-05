"""Projection Contract Tests for 6 more pure Projection-Shell sensors (HA-28 through HA-33).

All hit Core API endpoints only, no local semantic invention.
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


# ── ZoneModeSensor contract ────────────────────────────────────────────────

class ZoneModeSensorContract:
    """hits /api/v1/hub/modes"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        modes = self._data.get("active_modes", [])
        return ", ".join(sorted(modes)) if modes else "Standard"
    @property
    def extra_state_attributes(self):
        return {
            "active_modes": self._data.get("active_modes", []),
            "available_modes": self._data.get("available_modes", []),
        }


# ── DemandResponseSensor contract ──────────────────────────────────────────

_DR_ICONS = {"optimal": "mdi:leaf", "active": "mdi:flash", "inactive": "mdi:flash-off"}

class DemandResponseSensorContract:
    """hits /api/v1/energy/demand-response/status"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("status", "inactive")
    @property
    def icon(self):
        s = self._data.get("status", "inactive")
        return _DR_ICONS.get(s, "mdi:flash-off")
    @property
    def extra_state_attributes(self):
        return {
            "current_event": self._data.get("current_event"),
            "participants": self._data.get("participants", 0),
            "potential_savings_eur": self._data.get("potential_savings_eur"),
        }


# ── NotificationSensor contract ───────────────────────────────────────────

class NotificationSensorContract:
    """hits /api/v1/notifications"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("summary", "Keine Meldungen")
    @property
    def icon(self):
        count = self._data.get("unread_count", 0)
        return "mdi:bell-badge" if count > 0 else "mdi:bell-outline"
    @property
    def extra_state_attributes(self):
        return {
            "unread_count": self._data.get("unread_count", 0),
            "critical_count": self._data.get("critical_count", 0),
            "notifications": self._data.get("notifications", [])[:10],
        }


# ── ProactiveAlertSensor contract ──────────────────────────────────────────

_ALERT_ICONS = {"critical": "mdi:alert", "warning": "mdi:alert-outline", "info": "mdi:information", "none": "mdi:check-circle"}

class ProactiveAlertSensorContract:
    """hits /api/v1/regional (alerts endpoint)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        level = self._data.get("alert_level", "none")
        return level.capitalize()
    @property
    def icon(self):
        return _ALERT_ICONS.get(self._data.get("alert_level", "none"), "mdi:information")
    @property
    def extra_state_attributes(self):
        return {
            "alert_count": self._data.get("alert_count", 0),
            "alerts": self._data.get("alerts", []),
            "last_alert": self._data.get("last_alert"),
        }


# ── WeatherWarningSensor contract ──────────────────────────────────────────

class WeatherWarningSensorContract:
    """hits /api/v1/regional (warnings endpoint)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        level = self._data.get("severity", "none")
        return level.capitalize()
    @property
    def icon(self):
        icons = {"extreme": "mdi:weather-hurricane", "severe": "mdi:weather-lightning", "moderate": "mdi:weather-rainy", "minor": "mdi:weather-cloudy", "none": "mdi:weather-sunny"}
        return icons.get(self._data.get("severity", "none"), "mdi:weather-sunny")
    @property
    def extra_state_attributes(self):
        return {
            "warnings": self._data.get("warnings", []),
            "warn_count": self._data.get("warn_count", 0),
        }


# ── AnomalyAlertSensor contract ────────────────────────────────────────────

class AnomalyAlertSensorContract:
    """Coordinator-data passthrough via _handle_coordinator_update"""
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = coordinator.data
    @property
    def native_value(self):
        count = self._data.get("anomaly_count", 0)
        return count
    @property
    def extra_state_attributes(self):
        return {
            "anomaly_count": self._data.get("anomaly_count", 0),
            "top_anomaly": self._data.get("top_anomaly"),
            "severity": self._data.get("severity", "none"),
        }


# ── Tests: ZoneModeSensor ──────────────────────────────────────────────────

def test_ZM1_native_value_multi():
    s = ZoneModeSensorContract()
    s.apply({"ok": True, "active_modes": ["Abend", "Eco"]})
    assert s.native_value == "Abend, Eco"

def test_ZM2_native_value_empty():
    s = ZoneModeSensorContract()
    s.apply({"ok": True, "active_modes": []})
    assert s.native_value == "Standard"

def test_ZM3_attrs():
    s = ZoneModeSensorContract()
    s.apply({"ok": True, "active_modes": ["Abend"], "available_modes": ["Abend", "Eco", "Standard"]})
    attrs = s.extra_state_attributes
    assert attrs["active_modes"] == ["Abend"]
    assert attrs["available_modes"] == ["Abend", "Eco", "Standard"]


# ── Tests: DemandResponseSensor ─────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "status": "optimal"}, "optimal"),
    ({"ok": True, "status": "active"}, "active"),
    ({"ok": True, "status": "inactive"}, "inactive"),
    ({}, "inactive"),
])
def test_DR1_native_value(data, expected):
    s = DemandResponseSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "status": "optimal"}, "mdi:leaf"),
    ({"ok": True, "status": "active"}, "mdi:flash"),
    ({"ok": True, "status": "inactive"}, "mdi:flash-off"),
    ({}, "mdi:flash-off"),
])
def test_DR2_icon(data, expected_icon):
    s = DemandResponseSensorContract()
    s.apply(data)
    assert s.icon == expected_icon


# ── Tests: NotificationSensor ──────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "summary": "3 neue Meldungen"}, "3 neue Meldungen"),
    ({"ok": True, "summary": ""}, ""),
    ({}, "Keine Meldungen"),
])
def test_NS1_native_value(data, expected):
    s = NotificationSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "unread_count": 5}, "mdi:bell-badge"),
    ({"ok": True, "unread_count": 0}, "mdi:bell-outline"),
    ({}, "mdi:bell-outline"),
])
def test_NS2_icon(data, expected_icon):
    s = NotificationSensorContract()
    s.apply(data)
    assert s.icon == expected_icon

def test_NS3_attrs():
    s = NotificationSensorContract()
    s.apply({"ok": True, "unread_count": 3, "critical_count": 1, "notifications": [{"id": 1}]})
    attrs = s.extra_state_attributes
    assert attrs["unread_count"] == 3
    assert attrs["critical_count"] == 1
    assert len(attrs["notifications"]) == 1


# ── Tests: ProactiveAlertSensor ────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "alert_level": "critical"}, "Critical"),
    ({"ok": True, "alert_level": "warning"}, "Warning"),
    ({"ok": True, "alert_level": "info"}, "Info"),
    ({"ok": True, "alert_level": "none"}, "None"),
    ({}, "None"),
])
def test_PA1_native_value(data, expected):
    s = ProactiveAlertSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "alert_level": "critical"}, "mdi:alert"),
    ({"ok": True, "alert_level": "warning"}, "mdi:alert-outline"),
    ({"ok": True, "alert_level": "info"}, "mdi:information"),
    ({"ok": True, "alert_level": "none"}, "mdi:check-circle"),
])
def test_PA2_icon(data, expected_icon):
    s = ProactiveAlertSensorContract()
    s.apply(data)
    assert s.icon == expected_icon


# ── Tests: WeatherWarningSensor ────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "severity": "extreme"}, "Extreme"),
    ({"ok": True, "severity": "severe"}, "Severe"),
    ({"ok": True, "severity": "moderate"}, "Moderate"),
    ({"ok": True, "severity": "minor"}, "Minor"),
    ({"ok": True, "severity": "none"}, "None"),
    ({}, "None"),
])
def test_WW1_native_value(data, expected):
    s = WeatherWarningSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "severity": "extreme"}, "mdi:weather-hurricane"),
    ({"ok": True, "severity": "severe"}, "mdi:weather-lightning"),
    ({"ok": True, "severity": "moderate"}, "mdi:weather-rainy"),
    ({"ok": True, "severity": "minor"}, "mdi:weather-cloudy"),
    ({"ok": True, "severity": "none"}, "mdi:weather-sunny"),
])
def test_WW2_icon(data, expected_icon):
    s = WeatherWarningSensorContract()
    s.apply(data)
    assert s.icon == expected_icon


# ── Tests: AnomalyAlertSensor ──────────────────────────────────────────────

def test_AA1_native_value():
    coord = MockCoordinator({"anomaly_count": 5})
    s = AnomalyAlertSensorContract(coord)
    assert s.native_value == 5

def test_AA2_attrs():
    coord = MockCoordinator({"anomaly_count": 3, "top_anomaly": "sensor_x", "severity": "high"})
    s = AnomalyAlertSensorContract(coord)
    attrs = s.extra_state_attributes
    assert attrs["anomaly_count"] == 3
    assert attrs["top_anomaly"] == "sensor_x"
    assert attrs["severity"] == "high"
