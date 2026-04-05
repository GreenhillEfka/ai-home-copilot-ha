"""Projection Contract Tests for 7 more pure Projection-Shell sensors (HA-34 through HA-37).

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


# ── FuelPriceSensor contract ─────────────────────────────────────────────────

class FuelPriceSensorContract:
    """hits /api/v1/regional (fuel prices)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("current_price_ct_l")
    @property
    def extra_state_attributes(self):
        return {
            "fuel_type": self._data.get("fuel_type"),
            "currency": self._data.get("currency", "EUR"),
            "station": self._data.get("station"),
            "last_updated": self._data.get("last_updated"),
        }


# ── GasMeterSensor contract ─────────────────────────────────────────────────

class GasMeterSensorContract:
    """hits /api/v1/regional/gas"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("consumption_m3")
    @property
    def extra_state_attributes(self):
        return {
            "daily_m3": self._data.get("daily_m3"),
            "cost_eur": self._data.get("cost_eur"),
            "trend": self._data.get("trend"),
        }


# ── HeatPumpSensor contract ─────────────────────────────────────────────────

class HeatPumpSensorContract:
    """hits /api/v1/regional (heat pump data)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("cop")  # coefficient of performance
    @property
    def icon(self):
        mode = self._data.get("mode", "off")
        icons = {"heating": "mdi:fire", "cooling": "mdi:snowflake", "hot_water": "mdi:water", "off": "mdi:power"}
        return icons.get(mode, "mdi:thermometer")
    @property
    def extra_state_attributes(self):
        return {
            "mode": self._data.get("mode"),
            "flow_temp_c": self._data.get("flow_temp_c"),
            "return_temp_c": self._data.get("return_temp_c"),
            "power_kw": self._data.get("power_kw"),
            "energy_today_kwh": self._data.get("energy_today_kwh"),
        }


# ── EVChargingSensor contract ────────────────────────────────────────────────

class EVChargingSensorContract:
    """hits /api/v1/regional (EV charging data)"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("charge_level_pct")
    @property
    def icon(self):
        pct = self._data.get("charge_level_pct", 0)
        if pct >= 80:
            return "mdi:battery-charging-100"
        elif pct >= 50:
            return "mdi:battery-charging-70"
        elif pct >= 20:
            return "mdi:battery-charging-40"
        return "mdi:battery-charging-20"
    @property
    def extra_state_attributes(self):
        return {
            "charge_level_pct": self._data.get("charge_level_pct"),
            "charging_power_kw": self._data.get("charging_power_kw"),
            "time_to_full_min": self._data.get("time_to_full_min"),
            "status": self._data.get("status"),
        }


# ── EnergySankeySensor contract ─────────────────────────────────────────────

class EnergySankeySensorContract:
    """hits /api/v1/energy/sankey"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("total_consumption_kwh")
    @property
    def extra_state_attributes(self):
        return {
            "sankey_svg_url": "/api/v1/energy/sankey.svg",
            "sankey_json_url": "/api/v1/energy/sankey",
            "producers": self._data.get("producers", []),
            "consumers": self._data.get("consumers", []),
        }


# ── EnergyScheduleSensor contract ────────────────────────────────────────────

class EnergyScheduleSensorContract:
    """hits /api/v1/predict/schedule/daily"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("optimal_window_start", "N/A")
    @property
    def extra_state_attributes(self):
        return {
            "optimal_window_start": self._data.get("optimal_window_start"),
            "optimal_window_end": self._data.get("optimal_window_end"),
            "savings_eur": self._data.get("savings_eur"),
            "load_kw": self._data.get("load_kw"),
        }


# ── EnergyReportSensor contract ──────────────────────────────────────────────

class EnergyReportSensorContract:
    """hits /api/v1/energy/reports/generate"""
    def __init__(self):
        self._data = {}
    def apply(self, data):
        if data and data.get("ok"):
            self._data = data
    @property
    def native_value(self):
        return self._data.get("report_date", "No Report")
    @property
    def extra_state_attributes(self):
        return {
            "total_cost_eur": self._data.get("total_cost_eur"),
            "total_kwh": self._data.get("total_kwh"),
            "savings_eur": self._data.get("savings_eur"),
            "period": self._data.get("period"),
        }


# ── FuelPriceSensor tests ───────────────────────────────────────────────────

def test_FP1_native_value():
    s = FuelPriceSensorContract()
    s.apply({"ok": True, "current_price_ct_l": 165.5})
    assert s.native_value == 165.5

def test_FP2_native_value_none():
    s = FuelPriceSensorContract()
    s.apply({})
    assert s.native_value is None

def test_FP3_attrs():
    s = FuelPriceSensorContract()
    s.apply({"ok": True, "fuel_type": "diesel", "currency": "EUR", "station": "Shell", "last_updated": "2026-04-05T10:00:00Z"})
    attrs = s.extra_state_attributes
    assert attrs["fuel_type"] == "diesel"
    assert attrs["station"] == "Shell"


# ── GasMeterSensor tests ────────────────────────────────────────────────────

def test_GM1_native_value():
    s = GasMeterSensorContract()
    s.apply({"ok": True, "consumption_m3": 4.5})
    assert s.native_value == 4.5

def test_GM2_attrs():
    s = GasMeterSensorContract()
    s.apply({"ok": True, "daily_m3": 4.5, "cost_eur": 3.2, "trend": "stable"})
    attrs = s.extra_state_attributes
    assert attrs["daily_m3"] == 4.5
    assert attrs["cost_eur"] == 3.2
    assert attrs["trend"] == "stable"


# ── HeatPumpSensor tests ────────────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "cop": 4.2}, 4.2),
    ({"ok": True, "cop": None}, None),
    ({}, None),
])
def test_HP1_native_value(data, expected):
    s = HeatPumpSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "mode": "heating"}, "mdi:fire"),
    ({"ok": True, "mode": "cooling"}, "mdi:snowflake"),
    ({"ok": True, "mode": "hot_water"}, "mdi:water"),
    ({"ok": True, "mode": "off"}, "mdi:power"),
    ({"ok": True, "mode": ""}, "mdi:thermometer"),
])
def test_HP2_icon(data, expected_icon):
    s = HeatPumpSensorContract()
    s.apply(data)
    assert s.icon == expected_icon


# ── EVChargingSensor tests ─────────────────────────────────────────────────

@pytest.mark.parametrize("data,expected", [
    ({"ok": True, "charge_level_pct": 75}, 75),
    ({"ok": True, "charge_level_pct": 0}, 0),
    ({"ok": True, "charge_level_pct": 100}, 100),
    ({}, None),
])
def test_EV1_native_value(data, expected):
    s = EVChargingSensorContract()
    s.apply(data)
    assert s.native_value == expected

@pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "charge_level_pct": 85}, "mdi:battery-charging-100"),
    ({"ok": True, "charge_level_pct": 60}, "mdi:battery-charging-70"),
    ({"ok": True, "charge_level_pct": 30}, "mdi:battery-charging-40"),
    ({"ok": True, "charge_level_pct": 10}, "mdi:battery-charging-20"),
])
def test_EV2_icon(data, expected_icon):
    s = EVChargingSensorContract()
    s.apply(data)
    assert s.icon == expected_icon

def test_EV3_attrs():
    s = EVChargingSensorContract()
    s.apply({"ok": True, "charge_level_pct": 50, "charging_power_kw": 11.0, "time_to_full_min": 180, "status": "charging"})
    attrs = s.extra_state_attributes
    assert attrs["charging_power_kw"] == 11.0
    assert attrs["time_to_full_min"] == 180


# ── EnergySankeySensor tests ───────────────────────────────────────────────

def test_ES1_native_value():
    s = EnergySankeySensorContract()
    s.apply({"ok": True, "total_consumption_kwh": 45.0, "producers": [{"id": "pv"}], "consumers": [{"id": "heat_pump"}]})
    assert s.native_value == 45.0

def test_ES2_attrs():
    s = EnergySankeySensorContract()
    s.apply({"ok": True, "total_consumption_kwh": 45.0, "producers": [{"id": "pv"}], "consumers": [{"id": "heat_pump"}]})
    attrs = s.extra_state_attributes
    assert attrs["sankey_svg_url"] == "/api/v1/energy/sankey.svg"
    assert len(attrs["producers"]) == 1


# ── EnergyScheduleSensor tests ─────────────────────────────────────────────

def test_SS1_native_value():
    s = EnergyScheduleSensorContract()
    s.apply({"ok": True, "optimal_window_start": "02:00", "optimal_window_end": "05:00", "savings_eur": 1.8, "load_kw": 2.5})
    assert s.native_value == "02:00"

def test_SS2_attrs():
    s = EnergyScheduleSensorContract()
    s.apply({"ok": True, "optimal_window_start": "02:00", "optimal_window_end": "05:00", "savings_eur": 1.8, "load_kw": 2.5})
    attrs = s.extra_state_attributes
    assert attrs["optimal_window_end"] == "05:00"
    assert attrs["savings_eur"] == 1.8


# ── EnergyReportSensor tests ────────────────────────────────────────────────

def test_ER1_native_value():
    s = EnergyReportSensorContract()
    s.apply({"ok": True, "report_date": "2026-04-05", "total_cost_eur": 12.5, "total_kwh": 45.0, "savings_eur": 3.2, "period": "weekly"})
    assert s.native_value == "2026-04-05"

def test_ER2_attrs():
    s = EnergyReportSensorContract()
    s.apply({"ok": True, "report_date": "2026-04-05", "total_cost_eur": 12.5, "total_kwh": 45.0, "savings_eur": 3.2, "period": "weekly"})
    attrs = s.extra_state_attributes
    assert attrs["total_cost_eur"] == 12.5
    assert attrs["total_kwh"] == 45.0
    assert attrs["period"] == "weekly"
