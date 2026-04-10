"""Hub Dashboard Sensor Projection Contract Tests (HA-128, HA-317).

Verifiziert: HubDashboardSensor, HubPluginsSensor, HubMultiHomeSensor sind reine Projection-Shells
auf Core-APIs (/api/v1/hub/dashboard, /api/v1/hub/plugins, /api/v1/hub/homes).
"""

import inspect
import math
from unittest.mock import MagicMock, patch

import pytest


def _as_mapping(val, default=None):
    if isinstance(val, dict) and val:
        return val
    return default if default is not None else {}


def _as_list(val, default=None):
    if isinstance(val, list):
        return val
    return default if default is not None else []


def _as_string(val, default=""):
    if isinstance(val, str):
        normalized = val.strip()
        if normalized:
            return normalized
    return default


def _as_int(val, default=0):
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return int(val)
    return default


def _as_float(val, default=0.0):
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return float(val)
    return default


class HubDashboardSensorContract:
    """Mirror der Sensor-Logik für Test-Validierung."""

    @staticmethod
    def native_value(overview) -> int:
        data = _as_mapping(overview)
        return _as_int(data.get("active_devices"), 0)

    @staticmethod
    def icon(overview) -> str:
        data = _as_mapping(overview)
        alerts = _as_int(data.get("alerts_count"), 0)
        if alerts > 0:
            return "mdi:view-dashboard-alert"
        return "mdi:view-dashboard"

    @staticmethod
    def extra_state_attributes(overview) -> dict:
        data = _as_mapping(overview)
        summary = _as_mapping(data.get("summary"))
        return {
            "active_devices": _as_int(data.get("active_devices"), 0),
            "alerts_count": _as_int(data.get("alerts_count"), 0),
            "savings_today_eur": _as_float(data.get("savings_today_eur"), 0.0),
            "total_widgets": _as_int(summary.get("total_widgets"), 0),
            "layout_name": _as_string(summary.get("layout_name"), "default"),
            "theme": _as_string(summary.get("theme"), "auto"),
            "language": _as_string(summary.get("language"), "de"),
            "data_sources": _as_list(summary.get("data_sources"), []),
        }


class HubPluginsSensorContract:
    """Mirror der HubPluginsSensor-Logik."""

    @staticmethod
    def native_value(plugins) -> int:
        data = _as_mapping(plugins)
        return _as_int(data.get("active"), 0)

    @staticmethod
    def extra_state_attributes(plugins) -> dict:
        data = _as_mapping(plugins)
        return {
            "total": _as_int(data.get("total"), 0),
            "active": _as_int(data.get("active"), 0),
            "disabled": _as_int(data.get("disabled"), 0),
            "error": _as_int(data.get("error"), 0),
            "categories": _as_mapping(data.get("categories")),
        }


class HubMultiHomeSensorContract:
    """Mirror der HubMultiHomeSensor-Logik."""

    @staticmethod
    def native_value(homes) -> int:
        data = _as_mapping(homes)
        return _as_int(data.get("total_homes"), 0)

    @staticmethod
    def icon(homes) -> str:
        data = _as_mapping(homes)
        count = _as_int(data.get("total_homes"), 0)
        if count > 1:
            return "mdi:home-group"
        return "mdi:home"

    @staticmethod
    def extra_state_attributes(homes) -> dict:
        data = _as_mapping(homes)
        return {
            "total_homes": _as_int(data.get("total_homes"), 0),
            "online_homes": _as_int(data.get("online_homes"), 0),
            "total_devices": _as_int(data.get("total_devices"), 0),
            "total_energy_kwh": _as_float(data.get("total_energy_kwh"), 0.0),
            "total_cost_eur": _as_float(data.get("total_cost_eur"), 0.0),
            "active_home_id": _as_string(data.get("active_home_id"), ""),
        }


@pytest.fixture
def mock_coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession"):
    import custom_components.pilotsuite.sensors.hub_dashboard_sensor as hub_dashboard_module
    from custom_components.pilotsuite.sensors.hub_dashboard_sensor import (
        HubDashboardSensor,
        HubMultiHomeSensor,
        HubPluginsSensor,
    )


class TestHubDashboardSensor:
    """HD1–HD10: HubDashboardSensor Projection-Contract."""

    def test_HD1_native_value_active_devices(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 7, "alerts_count": 0, "savings_today_eur": 2.5}
        assert sensor.native_value == 7
        assert sensor.native_value == HubDashboardSensorContract.native_value(sensor._overview)

    def test_HD2_icon_with_alerts(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 5, "alerts_count": 3}
        assert sensor.icon == "mdi:view-dashboard-alert"

    def test_HD3_icon_no_alerts(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 5, "alerts_count": 0}
        assert sensor.icon == "mdi:view-dashboard"

    def test_HD4_extra_state_attributes_full(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {
            "active_devices": 12,
            "alerts_count": 1,
            "savings_today_eur": 5.75,
            "summary": {
                "total_widgets": 24,
                "layout_name": "main",
                "theme": "dark",
                "language": "de",
                "data_sources": ["core", "hass", "weather"],
            },
        }
        attrs = sensor.extra_state_attributes
        assert attrs == HubDashboardSensorContract.extra_state_attributes(sensor._overview)
        assert attrs["data_sources"] == ["core", "hass", "weather"]

    def test_HD5_edge_empty_dashboard(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {}
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:view-dashboard"
        assert sensor.extra_state_attributes == HubDashboardSensorContract.extra_state_attributes({})

    @pytest.mark.parametrize(
        "payload,expected_native,expected_icon",
        [
            ("offline", 0, "mdi:view-dashboard"),
            (None, 0, "mdi:view-dashboard"),
            (["bad"], 0, "mdi:view-dashboard"),
        ],
    )
    def test_HD6_non_dict_top_level_payload_defaults(self, mock_coordinator, payload, expected_native, expected_icon):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = payload
        assert sensor.native_value == expected_native
        assert sensor.icon == expected_icon
        assert sensor.extra_state_attributes == HubDashboardSensorContract.extra_state_attributes(payload)

    def test_HD7_malformed_numeric_payloads_fall_back(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {
            "active_devices": "7",
            "alerts_count": True,
            "savings_today_eur": float("inf"),
            "summary": {"total_widgets": float("nan")},
        }
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:view-dashboard"
        assert attrs["savings_today_eur"] == 0.0
        assert attrs["total_widgets"] == 0

    def test_HD8_float_counts_are_truncated(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {
            "active_devices": 7.9,
            "alerts_count": 1.2,
            "summary": {"total_widgets": 9.8},
        }
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 7
        assert sensor.icon == "mdi:view-dashboard-alert"
        assert attrs["total_widgets"] == 9

    def test_HD9_non_dict_summary_and_non_list_data_sources_default(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"summary": {"data_sources": "core", "layout_name": "   "}}
        attrs = sensor.extra_state_attributes
        assert attrs["layout_name"] == "default"
        assert attrs["data_sources"] == []

    def test_HD10_blank_summary_strings_default(self, mock_coordinator):
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {
            "summary": {"layout_name": "   ", "theme": "  ", "language": ""}
        }
        attrs = sensor.extra_state_attributes
        assert attrs["layout_name"] == "default"
        assert attrs["theme"] == "auto"
        assert attrs["language"] == "de"


class TestHubPluginsSensor:
    """HP1–HP8: HubPluginsSensor Projection-Contract."""

    def test_HP1_native_value_active_plugins(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"total": 10, "active": 8, "disabled": 2, "error": 0}
        assert sensor.native_value == 8

    def test_HP2_extra_state_attributes_full(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {
            "total": 15,
            "active": 12,
            "disabled": 2,
            "error": 1,
            "categories": {"sensor": 5, "switch": 3, "automation": 4},
        }
        assert sensor.extra_state_attributes == HubPluginsSensorContract.extra_state_attributes(sensor._plugins)

    def test_HP3_edge_empty_plugins(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {}
        assert sensor.native_value == 0
        assert sensor.extra_state_attributes == HubPluginsSensorContract.extra_state_attributes({})

    def test_HP4_non_dict_top_level_payload_defaults(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = "broken"
        assert sensor.native_value == 0
        assert sensor.extra_state_attributes == HubPluginsSensorContract.extra_state_attributes("broken")

    def test_HP5_string_and_bool_counts_default(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"total": "10", "active": True, "disabled": None, "error": float("nan")}
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 0
        assert attrs["total"] == 0
        assert attrs["active"] == 0
        assert attrs["disabled"] == 0
        assert attrs["error"] == 0

    def test_HP6_float_counts_truncate(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"active": 8.9, "total": 12.1, "disabled": 2.4, "error": 1.8}
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 8
        assert attrs["total"] == 12
        assert attrs["disabled"] == 2
        assert attrs["error"] == 1

    def test_HP7_non_dict_categories_default_to_empty_mapping(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"categories": ["sensor"]}
        assert sensor.extra_state_attributes["categories"] == {}

    def test_HP8_empty_categories_stays_empty_mapping(self, mock_coordinator):
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"categories": {}}
        assert sensor.extra_state_attributes["categories"] == {}


class TestHubMultiHomeSensor:
    """HM1–HM9: HubMultiHomeSensor Projection-Contract."""

    def test_HM1_native_value_total_homes(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 3, "online_homes": 2}
        assert sensor.native_value == 3

    def test_HM2_icon_single_home(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 1}
        assert sensor.icon == "mdi:home"

    def test_HM3_icon_multiple_homes(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 4}
        assert sensor.icon == "mdi:home-group"

    def test_HM4_extra_state_attributes_full(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {
            "total_homes": 5,
            "online_homes": 4,
            "total_devices": 120,
            "total_energy_kwh": 450.5,
            "total_cost_eur": 89.25,
            "active_home_id": "home-001",
        }
        assert sensor.extra_state_attributes == HubMultiHomeSensorContract.extra_state_attributes(sensor._homes)

    def test_HM5_edge_empty_homes(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {}
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:home"
        assert sensor.extra_state_attributes == HubMultiHomeSensorContract.extra_state_attributes({})

    def test_HM6_non_dict_top_level_payload_defaults(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = "broken"
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:home"
        assert sensor.extra_state_attributes == HubMultiHomeSensorContract.extra_state_attributes("broken")

    def test_HM7_malformed_numeric_payloads_default(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {
            "total_homes": "4",
            "online_homes": True,
            "total_devices": None,
            "total_energy_kwh": float("inf"),
            "total_cost_eur": float("nan"),
        }
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:home"
        assert attrs["online_homes"] == 0
        assert attrs["total_energy_kwh"] == 0.0
        assert attrs["total_cost_eur"] == 0.0

    def test_HM8_float_counts_truncate_and_blank_active_home_defaults(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {
            "total_homes": 2.9,
            "online_homes": 1.6,
            "total_devices": 12.4,
            "active_home_id": "   ",
        }
        attrs = sensor.extra_state_attributes
        assert sensor.native_value == 2
        assert sensor.icon == "mdi:home-group"
        assert attrs["online_homes"] == 1
        assert attrs["total_devices"] == 12
        assert attrs["active_home_id"] == ""

    def test_HM9_preserves_non_blank_active_home_id(self, mock_coordinator):
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"active_home_id": " home-001 "}
        assert sensor.extra_state_attributes["active_home_id"] == "home-001"


class TestGlobalContract:
    """GC1–GC3: Globale Projection-Contract-Garantien."""

    def test_GC1_hits_core_api_endpoints(self):
        source = inspect.getsource(hub_dashboard_module)
        assert "/api/v1/hub" in source
        assert 'f"{base}/dashboard"' in source
        assert 'f"{base}/plugins"' in source
        assert 'f"{base}/homes"' in source

    def test_GC2_projection_guards_are_present_in_source(self):
        source = inspect.getsource(hub_dashboard_module)
        assert "def _as_mapping" in source
        assert "def _as_list" in source
        assert "def _as_string" in source
        assert "def _as_int" in source
        assert "def _as_float" in source
        assert "math.isfinite" in source

    def test_GC3_no_local_semantic_invention_beyond_guarded_projection(self):
        source = inspect.getsource(hub_dashboard_module)
        assert 'return "mdi:view-dashboard-alert"' in source
        assert 'return "mdi:view-dashboard"' in source
        assert 'return "mdi:home-group"' in source
        assert 'return "mdi:home"' in source
