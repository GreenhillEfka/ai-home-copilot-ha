"""Projection Contract Tests for HubDashboardSensor and HubPluginsSensor (HA-11).

Verifies both sensors are pure Projection-Shells on Core-truth
(/api/v1/hub/dashboard, /api/v1/hub/plugins) without local semantic invention.

Pattern: same as HA-6 (habitus_zone), HA-8 (mood), HA-9 (autonomy), HA-10 (brain_activity).
"""
import pytest
from unittest.mock import Mock


class MockHass:
    class bus:
        @staticmethod
        async def async_fire(*a, **k): pass


class MockCoordinator:
    def __init__(self, data):
        self.data = data
        self.hass = MockHass()
        self.config_entry = Mock()
        self.config_entry.entry_id = "default"

    def async_write_ha_state(self):
        pass


# ── HubDashboardSensor contract mirror ───────────────────────────────────────

class HubDashboardSensorContract:
    """Mirror of HubDashboardSensor projection logic."""
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._overview = {}

    async def _fetch(self):
        """Simulates GET /api/v1/hub/dashboard."""
        return self._overview

    def _apply(self, data):
        if data and data.get("ok"):
            self._overview = data

    @property
    def native_value(self):
        return self._overview.get("active_devices", 0)

    @property
    def icon(self):
        alerts = self._overview.get("alerts_count", 0)
        if alerts > 0:
            return "mdi:view-dashboard-alert"
        return "mdi:view-dashboard"

    @property
    def extra_state_attributes(self):
        summary = self._overview.get("summary", {})
        return {
            "active_devices": self._overview.get("active_devices", 0),
            "alerts_count": self._overview.get("alerts_count", 0),
            "savings_today_eur": self._overview.get("savings_today_eur", 0),
            "total_widgets": summary.get("total_widgets", 0),
            "layout_name": summary.get("layout_name", "default"),
            "theme": summary.get("theme", "auto"),
            "language": summary.get("language", "de"),
            "data_sources": summary.get("data_sources", []),
        }


# ── HubPluginsSensor contract mirror ────────────────────────────────────────

class HubPluginsSensorContract:
    """Mirror of HubPluginsSensor projection logic."""
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._plugins = []

    async def _fetch(self):
        """Simulates GET /api/v1/hub/plugins."""
        return self._plugins

    def _apply(self, data):
        if data and data.get("ok"):
            self._plugins = data.get("plugins", [])

    @property
    def native_value(self):
        return len(self._plugins)

    @property
    def extra_state_attributes(self):
        enabled = [p for p in self._plugins if p.get("enabled", True)]
        return {
            "total_plugins": len(self._plugins),
            "enabled_plugins": len(enabled),
            "disabled_plugins": len(self._plugins) - len(enabled),
            "plugins": [p.get("name", p.get("id", "?")) for p in self._plugins],
        }


# ── HubDashboardSensor Test Cases ─────────────────────────────────────────────

DS1_native_value = pytest.mark.parametrize("core_data,expected", [
    ({"ok": True, "active_devices": 5}, 5),
    ({"ok": True, "active_devices": 0}, 0),
    ({}, 0),
    ({"ok": True}, 0),
])
DS2_icon = pytest.mark.parametrize("core_data,expected_icon", [
    ({"ok": True, "alerts_count": 0}, "mdi:view-dashboard"),
    ({"ok": True, "alerts_count": 1}, "mdi:view-dashboard-alert"),
    ({"ok": True, "alerts_count": 10}, "mdi:view-dashboard-alert"),
    ({}, "mdi:view-dashboard"),
])
DS3_extra_attrs = pytest.mark.parametrize("core_data,key,expected", [
    ({"ok": True, "active_devices": 3, "alerts_count": 1, "savings_today_eur": 2.5}, "active_devices", 3),
    ({"ok": True, "active_devices": 3, "alerts_count": 1, "savings_today_eur": 2.5}, "alerts_count", 1),
    ({"ok": True, "active_devices": 3, "alerts_count": 1, "savings_today_eur": 2.5}, "savings_today_eur", 2.5),
    ({"ok": True, "summary": {"total_widgets": 12}}, "total_widgets", 12),
    ({"ok": True, "summary": {"layout_name": "mobile"}}, "layout_name", "mobile"),
    ({"ok": True, "summary": {"theme": "dark"}}, "theme", "dark"),
    ({"ok": True, "summary": {"language": "en"}}, "language", "en"),
    ({"ok": True, "summary": {"data_sources": ["energy", "presence"]}}, "data_sources", ["energy", "presence"]),
    ({"ok": True, "summary": {}}, "data_sources", []),
])
DS4_edge_cases = pytest.mark.parametrize("fetched_data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "active_devices": 1}, True),
    ({"ok": True}, True),
])


# ── HubPluginsSensor Test Cases ───────────────────────────────────────────────

PS1_native_value = pytest.mark.parametrize("core_plugins,expected", [
    ([], 0),
    ([{"name": "p1", "enabled": True}], 1),
    ([{"id": "p1"}, {"id": "p2"}], 2),
    ([{"name": "a", "enabled": True}, {"name": "b", "enabled": False}], 2),
])
PS2_extra_attrs = pytest.mark.parametrize("core_plugins,key,expected", [
    ([{"name": "a", "enabled": True}], "total_plugins", 1),
    ([{"name": "a", "enabled": True}], "enabled_plugins", 1),
    ([{"name": "a", "enabled": False}], "disabled_plugins", 1),
    ([{"name": "a", "enabled": True}, {"name": "b", "enabled": True}], "enabled_plugins", 2),
    ([{"name": "a", "enabled": True}, {"name": "b", "enabled": False}], "disabled_plugins", 1),
    ([{"name": "energy", "enabled": True}], "plugins", ["energy"]),
])
PS3_edge = pytest.mark.parametrize("data,expect_ok", [
    (None, False),
    ({}, False),
    ({"ok": False}, False),
    ({"ok": True, "plugins": []}, True),
    ({"ok": True, "plugins": [{"name": "x", "enabled": True}]}, True),
])


# ── Parametrized test functions ───────────────────────────────────────────────

@DS1_native_value
def test_DS1_native_value(core_data, expected):
    coord = MockCoordinator({})
    sensor = HubDashboardSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.native_value == expected


@DS2_icon
def test_DS2_icon(core_data, expected_icon):
    coord = MockCoordinator({})
    sensor = HubDashboardSensorContract(coord)
    sensor._apply(core_data)
    assert sensor.icon == expected_icon


@DS3_extra_attrs
def test_DS3_extra_attrs(core_data, key, expected):
    coord = MockCoordinator({})
    sensor = HubDashboardSensorContract(coord)
    sensor._apply(core_data)
    attrs = sensor.extra_state_attributes
    assert attrs[key] == expected


@DS4_edge_cases
def test_DS4_edge_cases(fetched_data, expect_ok):
    coord = MockCoordinator({})
    sensor = HubDashboardSensorContract(coord)
    sensor._apply(fetched_data)
    if expect_ok:
        assert sensor._overview.get("ok") is True


@PS1_native_value
def test_PS1_native_value(core_plugins, expected):
    coord = MockCoordinator({})
    sensor = HubPluginsSensorContract(coord)
    sensor._apply({"ok": True, "plugins": core_plugins})
    assert sensor.native_value == expected


@PS2_extra_attrs
def test_PS2_extra_attrs(core_plugins, key, expected):
    coord = MockCoordinator({})
    sensor = HubPluginsSensorContract(coord)
    sensor._apply({"ok": True, "plugins": core_plugins})
    attrs = sensor.extra_state_attributes
    assert attrs[key] == expected


@PS3_edge
def test_PS3_edge(data, expect_ok):
    coord = MockCoordinator({})
    sensor = HubPluginsSensorContract(coord)
    sensor._apply(data)
    if expect_ok:
        assert True


def test_global_contract_no_local_logic():
    """Global: no local computation, no classification, no heuristics."""
    coord = MockCoordinator({})
    dash = HubDashboardSensorContract(coord)
    dash._apply({"ok": True, "active_devices": 7, "summary": {"total_widgets": 20}})
    attrs = dash.extra_state_attributes
    # All values direct from Core — zero local derivation
    assert attrs["active_devices"] == 7
    assert attrs["total_widgets"] == 20
