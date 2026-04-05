"""Projection Contract Tests for TariffSensor (HA-19a) and EnergyAdvisorSensor (HA-19b).

Verifies both are pure Projection-Shells on Core-truth without local semantic invention.
Pattern: same as HA-6 through HA-18.
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


# ── TariffSensor contract ─────────────────────────────────────────────────────

_LEVEL_ICONS = {
    "very_low": "mdi:lightning-bolt",
    "low": "mdi:flash",
    "normal": "mdi:flash-outline",
    "high": "mdi:flash-alert",
    "very_high": "mdi:flash-alert-outline",
}


class TariffSensorContract:
    """Mirror of TariffSensor projection logic.

    Contract:
    - hits /api/v1/regional/tariff/summary
    - native_value: current_price_ct_kwh
    - icon: _LEVEL_ICONS lookup
    - extra_state_attributes: direct passthrough + unit conversions (EUR→ct)
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        return self._data.get("current_price_ct_kwh")

    @property
    def icon(self):
        level = self._data.get("current_level", "normal")
        return _LEVEL_ICONS.get(level, "mdi:flash-outline")

    @property
    def extra_state_attributes(self):
        return {
            "current_price_eur_kwh": self._data.get("current_price_eur_kwh"),
            "current_level": self._data.get("current_level", ""),
            "avg_price_ct_kwh": round((self._data.get("avg_price_eur_kwh") or 0) * 100, 2),
            "min_price_ct_kwh": round((self._data.get("min_price_eur_kwh") or 0) * 100, 2),
            "max_price_ct_kwh": round((self._data.get("max_price_eur_kwh") or 0) * 100, 2),
            "min_hour": self._data.get("min_hour", ""),
            "max_hour": self._data.get("max_hour", ""),
            "spread_ct_kwh": round((self._data.get("spread_eur_kwh") or 0) * 100, 2),
            "tariff_type": self._data.get("tariff_type", ""),
            "source": self._data.get("source", ""),
            "hours_available": self._data.get("hours_available", 0),
        }


# ── EnergyAdvisorSensor contract ───────────────────────────────────────────────

_GRADE_ICONS = {
    "A+": "mdi:leaf",
    "A": "mdi:leaf",
    "B": "mdi:tree",
    "C": "mdi:flash",
    "D": "mdi:flash-alert",
    "E": "mdi:flash-alert-outline",
    "F": "mdi:lightning-bolt",
}


class EnergyAdvisorSensorContract:
    """Mirror of EnergyAdvisorSensor projection logic.

    Contract:
    - hits /api/v1/hub/energy
    - native_value: "Eco-Score {grade} ({score}/100)" or "Nicht verfügbar"
    - icon: _GRADE_ICONS lookup
    - extra_state_attributes: passthrough of eco_score + energy fields
    """
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        eco = self._data.get("eco_score", {})
        if not eco:
            return "Nicht verfügbar"
        grade = eco.get("grade", "?")
        score = eco.get("score", 0)
        return f"Eco-Score {grade} ({score}/100)"

    @property
    def icon(self):
        eco = self._data.get("eco_score", {})
        grade = eco.get("grade", "C")
        return _GRADE_ICONS.get(grade, "mdi:flash")

    @property
    def extra_state_attributes(self):
        eco = self._data.get("eco_score", {})
        attrs = {
            "eco_score": eco.get("score", 0),
            "eco_grade": eco.get("grade", "?"),
            "eco_trend": eco.get("trend", "stabil"),
            "total_daily_kwh": self._data.get("total_daily_kwh", 0),
        }
        return attrs


# ── TariffSensor test cases ───────────────────────────────────────────────────

TS1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "current_price_ct_kwh": 28.5}, 28.5),
    ({"ok": True, "current_price_ct_kwh": 0.0}, 0.0),
    ({"ok": True, "current_price_ct_kwh": 99.9}, 99.9),
    ({"ok": True, "current_price_ct_kwh": None}, None),
    ({}, None),
])
TS2 = pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "current_level": "very_low"}, "mdi:lightning-bolt"),
    ({"ok": True, "current_level": "low"}, "mdi:flash"),
    ({"ok": True, "current_level": "normal"}, "mdi:flash-outline"),
    ({"ok": True, "current_level": "high"}, "mdi:flash-alert"),
    ({"ok": True, "current_level": "very_high"}, "mdi:flash-alert-outline"),
    ({"ok": True, "current_level": ""}, "mdi:flash-outline"),
    ({"ok": True, "current_level": "unknown"}, "mdi:flash-outline"),
    ({}, "mdi:flash-outline"),
])
TS3 = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "avg_price_eur_kwh": 0.285, "min_price_eur_kwh": 0.20, "max_price_eur_kwh": 0.38, "spread_eur_kwh": 0.18}, "avg_price_ct_kwh", 28.5),
    ({"ok": True, "avg_price_eur_kwh": 0.285, "min_price_eur_kwh": 0.20, "max_price_eur_kwh": 0.38, "spread_eur_kwh": 0.18}, "min_price_ct_kwh", 20.0),
    ({"ok": True, "avg_price_eur_kwh": 0.285, "min_price_eur_kwh": 0.20, "max_price_eur_kwh": 0.38, "spread_eur_kwh": 0.18}, "max_price_ct_kwh", 38.0),
    ({"ok": True, "avg_price_eur_kwh": 0.285, "min_price_eur_kwh": 0.20, "max_price_eur_kwh": 0.38, "spread_eur_kwh": 0.18}, "spread_ct_kwh", 18.0),
    ({"ok": True, "tariff_type": "a_wattar", "source": "aWATTar", "hours_available": 24}, "tariff_type", "a_wattar"),
    ({"ok": True, "tariff_type": "a_wattar", "source": "aWATTar", "hours_available": 24}, "hours_available", 24),
])


# ── EnergyAdvisorSensor test cases ────────────────────────────────────────────

EA1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "eco_score": {"grade": "A", "score": 88}}, "Eco-Score A (88/100)"),
    ({"ok": True, "eco_score": {"grade": "B+", "score": 75}}, "Eco-Score B+ (75/100)"),
    ({"ok": True, "eco_score": {"grade": "F", "score": 15}}, "Eco-Score F (15/100)"),
    ({"ok": True, "eco_score": {}}, "Nicht verfügbar"),
    ({"ok": True}, "Nicht verfügbar"),
    ({}, "Nicht verfügbar"),
])
EA2 = pytest.mark.parametrize("data,expected_icon", [
    ({"ok": True, "eco_score": {"grade": "A+"}}, "mdi:leaf"),
    ({"ok": True, "eco_score": {"grade": "A"}}, "mdi:leaf"),
    ({"ok": True, "eco_score": {"grade": "B"}}, "mdi:tree"),
    ({"ok": True, "eco_score": {"grade": "C"}}, "mdi:flash"),
    ({"ok": True, "eco_score": {"grade": "D"}}, "mdi:flash-alert"),
    ({"ok": True, "eco_score": {"grade": "E"}}, "mdi:flash-alert-outline"),
    ({"ok": True, "eco_score": {"grade": "F"}}, "mdi:lightning-bolt"),
    ({"ok": True, "eco_score": {}}, "mdi:flash"),
    ({"ok": True}, "mdi:flash"),
])
EA3 = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "eco_score": {"grade": "A", "score": 90, "trend": "improving"}}, "eco_grade", "A"),
    ({"ok": True, "eco_score": {"grade": "A", "score": 90, "trend": "improving"}}, "eco_score", 90),
    ({"ok": True, "eco_score": {"grade": "A", "score": 90, "trend": "improving"}}, "eco_trend", "improving"),
    ({"ok": True, "total_daily_kwh": 12.5}, "total_daily_kwh", 12.5),
])


# ── Parametrized test functions ───────────────────────────────────────────────

@TS1
def test_TS1_native_value(data, expected):
    s = TariffSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@TS2
def test_TS2_icon(data, expected_icon):
    s = TariffSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.icon == expected_icon


@TS3
def test_TS3_attrs_unit_conversion(data, key, expected):
    s = TariffSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected


@EA1
def test_EA1_native_value(data, expected):
    s = EnergyAdvisorSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.native_value == expected


@EA2
def test_EA2_icon(data, expected_icon):
    s = EnergyAdvisorSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.icon == expected_icon


@EA3
def test_EA3_attrs(data, key, expected):
    s = EnergyAdvisorSensorContract(MockCoordinator({}))
    s.apply(data)
    assert s.extra_state_attributes[key] == expected
