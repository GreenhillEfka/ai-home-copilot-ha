"""Projection Contract Tests: proactive_alert_sensor.py

Verifies: ProactiveAlertSensor projects alert data fetched from Core API.
Uses _core_base_url() and _core_headers() — requires FakeResp mock + patch.

Contract verified:
- state = formatted alert summary
- attrs = processed alert list and priority/category breakdown
- Icon varies by highest priority level
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


class FakeResp:
    """Fake aiohttp response for patching Core API calls."""
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status = status

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


# === Fixtures ===

@pytest.fixture
def coordinator():
    c = MagicMock()
    c.data = {}
    c._config = {"host": "localhost", "port": 8909, "token": "test_token"}
    return c


@pytest.fixture
def sensor(coordinator):
    from custom_components.copilot_ha.sensors.proactive_alert_sensor import ProactiveAlertSensor
    return ProactiveAlertSensor(coordinator)


# === PA1: native_value ===

def test_proactive_alert_pa1_no_data(sensor):
    """PA1: No alert data → 'Keine Alerts'"""
    assert sensor.native_value == "Keine Alerts"


def test_proactive_alert_pa1_with_alerts(sensor):
    """PA1: With alerts → formatted summary"""
    sensor._data = {
        "total": 3,
        "highest_priority_label": "Warning",
    }
    assert sensor.native_value == "3x Warning"


def test_proactive_alert_pa1_single_alert(sensor):
    """PA1: Single alert → formatted summary"""
    sensor._data = {
        "total": 1,
        "highest_priority_label": "Critical",
    }
    assert sensor.native_value == "1x Critical"


# === PA2: icon ===

def test_proactive_alert_pa2_icon_priority_0(sensor):
    """PA2: Priority 0 → mdi:check-circle"""
    sensor._data = {"highest_priority": 0}
    assert sensor.icon == "mdi:check-circle"


def test_proactive_alert_pa2_icon_priority_1(sensor):
    """PA2: Priority 1 → mdi:information"""
    sensor._data = {"highest_priority": 1}
    assert sensor.icon == "mdi:information"


def test_proactive_alert_pa2_icon_priority_2(sensor):
    """PA2: Priority 2 → mdi:alert-outline"""
    sensor._data = {"highest_priority": 2}
    assert sensor.icon == "mdi:alert-outline"


def test_proactive_alert_pa2_icon_priority_3(sensor):
    """PA2: Priority 3 → mdi:alert"""
    sensor._data = {"highest_priority": 3}
    assert sensor.icon == "mdi:alert"


def test_proactive_alert_pa2_icon_priority_4(sensor):
    """PA2: Priority 4 → mdi:alert-octagon"""
    sensor._data = {"highest_priority": 4}
    assert sensor.icon == "mdi:alert-octagon"


def test_proactive_alert_pa2_icon_default(sensor):
    """PA2: Unknown priority → mdi:bell-alert (default)"""
    sensor._data = {"highest_priority": 99}
    assert sensor.icon == "mdi:bell-alert"


# === PA3: extra_state_attributes ===

def test_proactive_alert_pa3_attrs_structure(sensor):
    """PA3: attrs contain alert summary and breakdown"""
    sensor._data = {
        "total": 5,
        "highest_priority": 3,
        "highest_priority_label": "Warning",
        "by_priority": {
            "info": 1,
            "advisory": 1,
            "warning": 2,
            "critical": 1,
        },
        "by_category": {
            "weather": 2,
            "price": 2,
            "grid": 1,
        },
        "alerts": [
            {
                "title_de": "Sturmwarnung",
                "priority_label": "critical",
                "category": "weather",
                "action": "close_windows",
                "message_de": "Starke Winde erwartet",
                "icon": "mdi:weather-windy",
            },
        ],
        "last_evaluated": "2024-01-15T10:00:00Z",
    }
    attrs = sensor.extra_state_attributes
    assert attrs["total_alerts"] == 5
    assert attrs["highest_priority"] == 3
    assert attrs["highest_priority_label"] == "Warning"
    assert attrs["info_count"] == 1
    assert attrs["advisory_count"] == 1
    assert attrs["warning_count"] == 2
    assert attrs["critical_count"] == 1
    assert attrs["categories"] == {"weather": 2, "price": 2, "grid": 1}
    assert len(attrs["alerts"]) == 1
    assert attrs["alerts"][0]["title"] == "Sturmwarnung"
    assert attrs["last_evaluated"] == "2024-01-15T10:00:00Z"


def test_proactive_alert_pa3_empty_alerts(sensor):
    """PA3: Empty alerts list → empty alert_list in attrs"""
    sensor._data = {
        "total": 0,
        "alerts": [],
        "by_priority": {},
        "by_category": {},
    }
    attrs = sensor.extra_state_attributes
    assert attrs["total_alerts"] == 0
    assert attrs["alerts"] == []


def test_proactive_alert_pa3_alert_limiting(sensor):
    """PA3: Maximum 10 alerts in attrs"""
    sensor._data = {
        "total": 15,
        "alerts": [{"title_de": f"Alert {i}"} for i in range(15)],
        "by_priority": {},
        "by_category": {},
    }
    attrs = sensor.extra_state_attributes
    assert len(attrs["alerts"]) == 10


# === PA4: async_update ===

@pytest.mark.asyncio
async def test_proactive_alert_pa4_fetch_success(sensor):
    """PA4: async_update fetches alerts from Core API"""
    response_data = {
        "ok": True,
        "total": 2,
        "highest_priority": 2,
        "highest_priority_label": "Advisory",
        "alerts": [],
        "by_priority": {},
        "by_category": {},
    }
    with patch("aiohttp.ClientSession.get", return_value=FakeResp(response_data)):
        await sensor.async_update()
        assert sensor._data == response_data


@pytest.mark.asyncio
async def test_proactive_alert_pa4_fetch_not_ok(sensor):
    """PA4: Response ok=False → data not updated"""
    response_data = {"ok": False}
    with patch("aiohttp.ClientSession.get", return_value=FakeResp(response_data)):
        await sensor.async_update()
        assert sensor._data == {}  # Not updated


@pytest.mark.asyncio
async def test_proactive_alert_pa4_fetch_error_status(sensor):
    """PA4: Non-200 status → data not updated"""
    with patch("aiohttp.ClientSession.get", return_value=FakeResp({}, status=500)):
        await sensor.async_update()
        assert sensor._data == {}


@pytest.mark.asyncio
async def test_proactive_alert_pa4_fetch_exception(sensor):
    """PA4: Exception during fetch → data not updated"""
    with patch("aiohttp.ClientSession.get", side_effect=Exception("Connection error")):
        await sensor.async_update()
        assert sensor._data == {}


# === PA5: Sensor configuration ===

def test_proactive_alert_pa5_sensor_config(sensor):
    """PA5: ProactiveAlertSensor has correct configuration"""
    assert sensor._attr_name == "Proactive Alerts"
    assert sensor._attr_unique_id == "copilot_proactive_alerts"
    assert sensor._attr_icon == "mdi:bell-alert"


# === GC: Global Contract ===

def test_proactive_alert_gc1_projection_from_api_data(sensor):
    """GC1: Sensor state derived from API response projection"""
    sensor._data = {
        "total": 4,
        "highest_priority": 3,
        "highest_priority_label": "Warning",
        "by_priority": {"warning": 3, "critical": 1},
        "by_category": {"weather": 2, "grid": 2},
        "alerts": [
            {"title_de": "Test", "priority_label": "warning", "category": "weather"},
        ],
        "last_evaluated": "2024-01-15T10:00:00Z",
    }
    assert sensor.native_value == "4x Warning"
    attrs = sensor.extra_state_attributes
    assert attrs["total_alerts"] == 4
    assert attrs["warning_count"] == 3
    assert attrs["categories"]["weather"] == 2


def test_proactive_alert_gc2_icon_reflects_priority(sensor):
    """GC2: Icon dynamically reflects highest priority level"""
    for priority, expected_icon in [
        (0, "mdi:check-circle"),
        (1, "mdi:information"),
        (2, "mdi:alert-outline"),
        (3, "mdi:alert"),
        (4, "mdi:alert-octagon"),
    ]:
        sensor._data = {"highest_priority": priority}
        assert sensor.icon == expected_icon, f"Priority {priority} should show {expected_icon}"
