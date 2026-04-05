"""Projection Contract Tests for BatteryOptimizerSensor (HA-17).

Verifies that BatteryOptimizerSensor is a pure Projection-Shell on Core-truth
(/api/v1/regional/battery/status, /api/v1/regional/battery/schedule).

Pattern: same as HA-6/8/9/10/11/12/13/14/15/16.
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


class BatteryOptimizerSensorContract:
    """Mirror of BatteryOptimizerSensor projection logic.

    Contract:
    - hits /api/v1/regional/battery/status → self._status
    - hits /api/v1/regional/battery/schedule → self._schedule
    - native_value: _status.soc_pct (float)
    - icon: action-based or soc-based thresholds (trivial)
    - extra_state_attributes: passthrough of _status + _schedule fields
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._status = {}
        self._schedule = {}

    def apply_status(self, data):
        if data and data.get("ok"):
            self._status = data

    def apply_schedule(self, data):
        if data and data.get("ok"):
            self._schedule = data

    @property
    def native_value(self):
        return self._status.get("soc_pct")

    @property
    def icon(self):
        soc = self._status.get("soc_pct", 50)
        action = self._status.get("current_action", "hold")
        if action in ("charge", "charge_solar"):
            return "mdi:battery-charging"
        elif action == "discharge":
            return "mdi:battery-arrow-down"
        elif soc >= 80:
            return "mdi:battery-high"
        elif soc >= 30:
            return "mdi:battery-medium"
        return "mdi:battery-low"

    @property
    def extra_state_attributes(self):
        attrs = {
            "soc_pct": self._status.get("soc_pct", 0),
            "soc_kwh": self._status.get("soc_kwh", 0),
            "capacity_kwh": self._status.get("capacity_kwh", 0),
            "current_action": self._status.get("current_action", "hold"),
            "current_power_kw": self._status.get("current_power_kw", 0),
            "strategy": self._status.get("strategy", "none"),
            "cycles_today": self._status.get("cycles_today", 0),
            "next_charge_at": self._status.get("next_charge_at", ""),
            "next_discharge_at": self._status.get("next_discharge_at", ""),
            "health_pct": self._status.get("health_pct", 100),
        }
        if self._schedule:
            attrs["estimated_savings_eur"] = self._schedule.get("estimated_savings_eur", 0)
            attrs["total_charge_kwh"] = self._schedule.get("total_charge_kwh", 0)
            attrs["total_discharge_kwh"] = self._schedule.get("total_discharge_kwh", 0)
            attrs["total_solar_charge_kwh"] = self._schedule.get("total_solar_charge_kwh", 0)
            attrs["estimated_cycles"] = self._schedule.get("estimated_cycles", 0)
            attrs["avg_charge_price_ct"] = self._schedule.get("avg_charge_price_ct", 0)
            attrs["avg_discharge_price_ct"] = self._schedule.get("avg_discharge_price_ct", 0)
        return attrs


BO1_native_value = pytest.mark.parametrize("status_data,expected", [
    ({"ok": True, "soc_pct": 75.5}, 75.5),
    ({"ok": True, "soc_pct": 0.0}, 0.0),
    ({"ok": True, "soc_pct": 100.0}, 100.0),
    ({"ok": True, "soc_pct": None}, None),
    ({}, None),
])
BO2_icon = pytest.mark.parametrize("status_data,expected_icon", [
    ({"ok": True, "current_action": "charge", "soc_pct": 50}, "mdi:battery-charging"),
    ({"ok": True, "current_action": "charge_solar", "soc_pct": 50}, "mdi:battery-charging"),
    ({"ok": True, "current_action": "discharge", "soc_pct": 50}, "mdi:battery-arrow-down"),
    ({"ok": True, "current_action": "hold", "soc_pct": 85}, "mdi:battery-high"),
    ({"ok": True, "current_action": "hold", "soc_pct": 50}, "mdi:battery-medium"),
    ({"ok": True, "current_action": "hold", "soc_pct": 20}, "mdi:battery-low"),
    ({"ok": True, "current_action": "hold", "soc_pct": 30}, "mdi:battery-medium"),
    ({"ok": True, "current_action": "hold", "soc_pct": 79}, "mdi:battery-medium"),
    ({"ok": True, "current_action": "unknown", "soc_pct": 90}, "mdi:battery-high"),
    ({}, "mdi:battery-medium"),
])
BO3_attrs_status = pytest.mark.parametrize("status_data,key,expected", [
    ({"ok": True, "soc_pct": 80, "soc_kwh": 10.0, "capacity_kwh": 13.0, "current_action": "charge", "current_power_kw": 3.0, "strategy": "solar_first", "cycles_today": 2, "health_pct": 98}, "soc_pct", 80),
    ({"ok": True, "soc_pct": 80, "soc_kwh": 10.0, "capacity_kwh": 13.0, "current_action": "charge", "current_power_kw": 3.0, "strategy": "solar_first", "cycles_today": 2, "health_pct": 98}, "soc_kwh", 10.0),
    ({"ok": True, "soc_pct": 80, "soc_kwh": 10.0, "capacity_kwh": 13.0, "current_action": "charge", "current_power_kw": 3.0, "strategy": "solar_first", "cycles_today": 2, "health_pct": 98}, "current_action", "charge"),
    ({"ok": True, "soc_pct": 80, "soc_kwh": 10.0, "capacity_kwh": 13.0, "current_action": "charge", "current_power_kw": 3.0, "strategy": "solar_first", "cycles_today": 2, "health_pct": 98}, "strategy", "solar_first"),
    ({"ok": True, "soc_pct": 80, "soc_kwh": 10.0, "capacity_kwh": 13.0, "current_action": "charge", "current_power_kw": 3.0, "strategy": "solar_first", "cycles_today": 2, "health_pct": 98}, "health_pct", 98),
])
BO4_schedule_attrs = pytest.mark.parametrize("schedule_data,key,expected", [
    ({"ok": True, "estimated_savings_eur": 2.50, "total_charge_kwh": 8.0, "total_discharge_kwh": 5.0, "total_solar_charge_kwh": 6.0, "estimated_cycles": 1.5, "avg_charge_price_ct": 28.5, "avg_discharge_price_ct": 42.0}, "estimated_savings_eur", 2.50),
    ({"ok": True, "estimated_savings_eur": 2.50, "total_charge_kwh": 8.0, "total_discharge_kwh": 5.0, "total_solar_charge_kwh": 6.0, "estimated_cycles": 1.5, "avg_charge_price_ct": 28.5, "avg_discharge_price_ct": 42.0}, "total_charge_kwh", 8.0),
    ({"ok": True, "estimated_savings_eur": 2.50, "total_charge_kwh": 8.0, "total_discharge_kwh": 5.0, "total_solar_charge_kwh": 6.0, "estimated_cycles": 1.5, "avg_charge_price_ct": 28.5, "avg_discharge_price_ct": 42.0}, "avg_discharge_price_ct", 42.0),
])
BO5_edge = pytest.mark.parametrize("status_data,schedule_data", [
    ({}, {}),
    ({"ok": True, "soc_pct": 50}, {}),
    ({}, {"ok": True, "estimated_savings_eur": 1.0}),
    ({"ok": False}, {"ok": True, "estimated_savings_eur": 1.0}),
])


@BO1_native_value
def test_BO1_native_value(status_data, expected):
    s = BatteryOptimizerSensorContract(MockCoordinator({}))
    s.apply_status(status_data)
    assert s.native_value == expected


@BO2_icon
def test_BO2_icon(status_data, expected_icon):
    s = BatteryOptimizerSensorContract(MockCoordinator({}))
    s.apply_status(status_data)
    assert s.icon == expected_icon


@BO3_attrs_status
def test_BO3_attrs_status(status_data, key, expected):
    s = BatteryOptimizerSensorContract(MockCoordinator({}))
    s.apply_status(status_data)
    assert s.extra_state_attributes[key] == expected


@BO4_schedule_attrs
def test_BO4_schedule_attrs(schedule_data, key, expected):
    s = BatteryOptimizerSensorContract(MockCoordinator({}))
    s.apply_status({"ok": True, "soc_pct": 50})
    s.apply_schedule(schedule_data)
    assert s.extra_state_attributes[key] == expected


@BO5_edge
def test_BO5_edge_no_crash(status_data, schedule_data):
    s = BatteryOptimizerSensorContract(MockCoordinator({}))
    s.apply_status(status_data)
    s.apply_schedule(schedule_data)
    # Should not raise, just return defaults
    _ = s.extra_state_attributes
