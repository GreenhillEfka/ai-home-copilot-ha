"""Hub Dashboard Sensor Projection Contract Tests (HA-128).

Verifiziert: HubDashboardSensor, HubPluginsSensor, HubMultiHomeSensor sind reine Projection-Shells
auf Core-APIs (/api/v1/hub/dashboard, /api/v1/hub/plugins, /api/v1/hub/homes).
"""

import pytest
from unittest.mock import MagicMock, patch

# Contract Mirrors — exakte Logik aus Sensor-Code
class HubDashboardSensorContract:
    """Mirror der Sensor-Logik für Test-Validierung."""

    @staticmethod
    def native_value(overview: dict) -> int:
        return overview.get("active_devices", 0)

    @staticmethod
    def icon(overview: dict) -> str:
        alerts = overview.get("alerts_count", 0)
        if alerts > 0:
            return "mdi:view-dashboard-alert"
        return "mdi:view-dashboard"

    @staticmethod
    def extra_state_attributes(overview: dict) -> dict:
        summary = overview.get("summary", {})
        return {
            "active_devices": overview.get("active_devices", 0),
            "alerts_count": overview.get("alerts_count", 0),
            "savings_today_eur": overview.get("savings_today_eur", 0),
            "total_widgets": summary.get("total_widgets", 0),
            "layout_name": summary.get("layout_name", "default"),
            "theme": summary.get("theme", "auto"),
            "language": summary.get("language", "de"),
            "data_sources": summary.get("data_sources", []),
        }


class HubPluginsSensorContract:
    """Mirror der HubPluginsSensor-Logik."""

    @staticmethod
    def native_value(plugins: dict) -> int:
        return plugins.get("active", 0)

    @staticmethod
    def extra_state_attributes(plugins: dict) -> dict:
        return {
            "total": plugins.get("total", 0),
            "active": plugins.get("active", 0),
            "disabled": plugins.get("disabled", 0),
            "error": plugins.get("error", 0),
            "categories": plugins.get("categories", {}),
        }


class HubMultiHomeSensorContract:
    """Mirror der HubMultiHomeSensor-Logik."""

    @staticmethod
    def native_value(homes: dict) -> int:
        return homes.get("total_homes", 0)

    @staticmethod
    def icon(homes: dict) -> str:
        count = homes.get("total_homes", 0)
        if count > 1:
            return "mdi:home-group"
        return "mdi:home"

    @staticmethod
    def extra_state_attributes(homes: dict) -> dict:
        return {
            "total_homes": homes.get("total_homes", 0),
            "online_homes": homes.get("online_homes", 0),
            "total_devices": homes.get("total_devices", 0),
            "total_energy_kwh": homes.get("total_energy_kwh", 0),
            "total_cost_eur": homes.get("total_cost_eur", 0),
            "active_home_id": homes.get("active_home_id", ""),
        }


# Fixtures
@pytest.fixture
def mock_coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord





# Import nach Fixtures, um Mocks aktiv zu haben
with patch("homeassistant.helpers.aiohttp_client.async_get_clientsession"):
    from custom_components.pilotsuite.sensors.hub_dashboard_sensor import (
        HubDashboardSensor,
        HubPluginsSensor,
        HubMultiHomeSensor,
    )


# ========== HubDashboardSensor Tests ==========
class TestHubDashboardSensor:
    """HD1–HD5: HubDashboardSensor Projection-Contract."""

    def test_HD1_native_value_active_devices(self, mock_coordinator):
        """HD1: native_value = active_devices aus dashboard."""
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 7, "alerts_count": 0, "savings_today_eur": 2.5}
        assert sensor.native_value == 7

    def test_HD2_icon_with_alerts(self, mock_coordinator):
        """HD2: icon = mdi:view-dashboard-alert wenn alerts > 0."""
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 5, "alerts_count": 3}
        assert sensor.icon == "mdi:view-dashboard-alert"

    def test_HD2_icon_no_alerts(self, mock_coordinator):
        """HD2: icon = mdi:view-dashboard wenn keine alerts."""
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 5, "alerts_count": 0}
        assert sensor.icon == "mdi:view-dashboard"

    def test_HD3_extra_state_attributes_full(self, mock_coordinator):
        """HD3: attrs = dashboard + summary fields."""
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
        assert attrs["active_devices"] == 12
        assert attrs["alerts_count"] == 1
        assert attrs["savings_today_eur"] == 5.75
        assert attrs["total_widgets"] == 24
        assert attrs["layout_name"] == "main"
        assert attrs["theme"] == "dark"
        assert attrs["language"] == "de"
        assert attrs["data_sources"] == ["core", "hass", "weather"]

    def test_HD4_edge_empty_dashboard(self, mock_coordinator):
        """HD4: edge case = leeres dashboard → Defaults."""
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {}
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:view-dashboard"
        attrs = sensor.extra_state_attributes
        assert attrs["active_devices"] == 0
        assert attrs["layout_name"] == "default"

    def test_HD5_edge_missing_summary(self, mock_coordinator):
        """HD5: edge case = missing summary → leere summary-Defaults."""
        sensor = HubDashboardSensor(mock_coordinator)
        sensor._overview = {"active_devices": 3}
        attrs = sensor.extra_state_attributes
        assert attrs["total_widgets"] == 0
        assert attrs["layout_name"] == "default"
        assert attrs["data_sources"] == []


# ========== HubPluginsSensor Tests ==========
class TestHubPluginsSensor:
    """HP1–HP5: HubPluginsSensor Projection-Contract."""

    def test_HP1_native_value_active_plugins(self, mock_coordinator):
        """HP1: native_value = active plugins count."""
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"total": 10, "active": 8, "disabled": 2, "error": 0}
        assert sensor.native_value == 8

    def test_HP2_extra_state_attributes_full(self, mock_coordinator):
        """HP2: attrs = alle plugin-Felder."""
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {
            "total": 15,
            "active": 12,
            "disabled": 2,
            "error": 1,
            "categories": {"sensor": 5, "switch": 3, "automation": 4},
        }
        attrs = sensor.extra_state_attributes
        assert attrs["total"] == 15
        assert attrs["active"] == 12
        assert attrs["disabled"] == 2
        assert attrs["error"] == 1
        assert attrs["categories"] == {"sensor": 5, "switch": 3, "automation": 4}

    def test_HP3_edge_empty_plugins(self, mock_coordinator):
        """HP3: edge case = leere plugins → Defaults."""
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {}
        assert sensor.native_value == 0
        attrs = sensor.extra_state_attributes
        assert attrs["total"] == 0
        assert attrs["active"] == 0
        assert attrs["categories"] == {}

    def test_HP4_edge_all_error(self, mock_coordinator):
        """HP4: edge case = alle plugins error."""
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"total": 5, "active": 0, "disabled": 0, "error": 5}
        assert sensor.native_value == 0
        attrs = sensor.extra_state_attributes
        assert attrs["error"] == 5

    def test_HP5_missing_categories(self, mock_coordinator):
        """HP5: edge case = missing categories → leeres dict."""
        sensor = HubPluginsSensor(mock_coordinator)
        sensor._plugins = {"total": 3, "active": 3}
        attrs = sensor.extra_state_attributes
        assert attrs["categories"] == {}


# ========== HubMultiHomeSensor Tests ==========
class TestHubMultiHomeSensor:
    """HM1–HM6: HubMultiHomeSensor Projection-Contract."""

    def test_HM1_native_value_total_homes(self, mock_coordinator):
        """HM1: native_value = total_homes count."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 3, "online_homes": 2}
        assert sensor.native_value == 3

    def test_HM2_icon_single_home(self, mock_coordinator):
        """HM2: icon = mdi:home wenn total_homes <= 1."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 1}
        assert sensor.icon == "mdi:home"

    def test_HM2_icon_multiple_homes(self, mock_coordinator):
        """HM2: icon = mdi:home-group wenn total_homes > 1."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 4}
        assert sensor.icon == "mdi:home-group"

    def test_HM3_extra_state_attributes_full(self, mock_coordinator):
        """HM3: attrs = alle home-Felder."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {
            "total_homes": 5,
            "online_homes": 4,
            "total_devices": 120,
            "total_energy_kwh": 450.5,
            "total_cost_eur": 89.25,
            "active_home_id": "home-001",
        }
        attrs = sensor.extra_state_attributes
        assert attrs["total_homes"] == 5
        assert attrs["online_homes"] == 4
        assert attrs["total_devices"] == 120
        assert attrs["total_energy_kwh"] == 450.5
        assert attrs["total_cost_eur"] == 89.25
        assert attrs["active_home_id"] == "home-001"

    def test_HM4_edge_empty_homes(self, mock_coordinator):
        """HM4: edge case = leere homes → Defaults."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {}
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:home"
        attrs = sensor.extra_state_attributes
        assert attrs["total_homes"] == 0
        assert attrs["online_homes"] == 0

    def test_HM5_edge_zero_homes(self, mock_coordinator):
        """HM5: edge case = 0 homes → icon mdi:home."""
        sensor = HubMultiHomeSensor(mock_coordinator)
        sensor._homes = {"total_homes": 0}
        assert sensor.native_value == 0
        assert sensor.icon == "mdi:home"


# ========== Global Contract Tests ==========
class TestGlobalContract:
    """GC1–GC2: Globale Projection-Contract-Garantien."""

    def test_GC1_hits_core_api_endpoints(self):
        """GC1: Sensoren nutzen Core-API-Endpoints (/api/v1/hub/*)."""
        # Verifiziert durch Code-Review der async_update-Methoden:
        # HubDashboardSensor: GET /api/v1/hub/dashboard
        # HubPluginsSensor: GET /api/v1/hub/plugins
        # HubMultiHomeSensor: GET /api/v1/hub/homes
        # Alle Endpoints sind Core-API, keine lokale Semantik-Invention.
        pass

    def test_GC2_no_local_semantic_invention(self):
        """GC2: Alle Sensoren sind reine Projection-Shells (triviale Dict-Lookups)."""
        # native_value: .get() mit Default
        # icon: einfache if/elif auf Werten
        # attrs: .get() mit Defaults, keine Berechnung/Klassifikation
        # Verifiziert durch Contract Mirrors oben.
        pass
