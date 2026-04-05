"""Projection Contract Tests for EnergyCostSensor (HA-25), EnergyForecastSensor (HA-26), and EnergyInsightsSensor (HA-27).

All three are pure Projection-Shells on Core-truth.
Pattern: same as HA-6 through HA-24.
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


# ── EnergyCostSensor contract ────────────────────────────────────────────────

class EnergyCostSensorContract:
    """Mirror of EnergyCostSensor projection logic.

    Contract:
    - hits /api/v1/energy/costs/summary?period=weekly + /api/v1/energy/costs/budget
    - native_value: total_cost_eur from summary
    - extra_state_attributes: direct passthrough of summary + budget fields
    """
    def __init__(self):
        self._summary_data = None
        self._budget_data = None

    def apply_summary(self, data):
        if data and data.get("ok"):
            self._summary_data = data

    def apply_budget(self, data):
        if data and data.get("ok"):
            self._budget_data = data

    @property
    def native_value(self):
        if self._summary_data and self._summary_data.get("ok"):
            return self._summary_data.get("total_cost_eur")
        return None

    @property
    def extra_state_attributes(self):
        attrs = {
            "costs_url": "/api/v1/energy/costs",
            "budget_url": "/api/v1/energy/costs/budget",
        }
        if self._summary_data and self._summary_data.get("ok"):
            attrs["period"] = self._summary_data.get("period")
            attrs["avg_daily_cost_eur"] = self._summary_data.get("avg_daily_cost_eur")
            attrs["total_consumption_kwh"] = self._summary_data.get("total_consumption_kwh")
            attrs["total_savings_eur"] = self._summary_data.get("total_savings_eur")
            attrs["days_count"] = self._summary_data.get("days_count")
        if self._budget_data and self._budget_data.get("ok"):
            attrs["budget_eur"] = self._budget_data.get("budget_eur")
            attrs["budget_spent_eur"] = self._budget_data.get("spent_eur")
            attrs["budget_remaining_eur"] = self._budget_data.get("remaining_eur")
            attrs["budget_percent_used"] = self._budget_data.get("percent_used")
            attrs["budget_on_track"] = self._budget_data.get("on_track")
            attrs["budget_projected_eur"] = self._budget_data.get("projected_total_eur")
        return attrs


# ── EnergyForecastSensor contract ──────────────────────────────────────────

class EnergyForecastSensorContract:
    """Mirror of EnergyForecastSensor projection logic.

    Contract:
    - hits /api/v1/energy/forecast?horizon={n}
    - native_value: forecast_total_kwh
    - extra_state_attributes: passthrough of forecast fields
    """
    def __init__(self):
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        if self._data and self._data.get("ok"):
            return self._data.get("forecast_total_kwh")
        return None

    @property
    def extra_state_attributes(self):
        return {
            "forecast_date": self._data.get("date"),
            "horizon_hours": self._data.get("horizon_hours"),
            "forecast_cost_eur": self._data.get("forecast_cost_eur"),
            "confidence_pct": self._data.get("confidence_pct"),
            "model_used": self._data.get("model_used"),
        }


# ── EnergyInsightsSensor contract ──────────────────────────────────────────

class EnergyInsightsSensorContract:
    """Mirror of EnergyInsightsSensor projection logic.

    Contract:
    - hits /api/v1/energy/insights
    - native_value: insight_count
    - extra_state_attributes: passthrough of insights list
    """
    def __init__(self):
        self._data = {}

    def apply(self, data):
        if data and data.get("ok"):
            self._data = data

    @property
    def native_value(self):
        if self._data and self._data.get("ok"):
            insights = self._data.get("insights")
            if insights is None:
                return 0
            return len(insights)
        return 0

    @property
    def extra_state_attributes(self):
        return {
            "insights": self._data.get("insights", []),
            "has_critical": self._data.get("has_critical", False),
            "has_warnings": self._data.get("has_warnings", False),
        }


# ── EnergyCostSensor test cases ─────────────────────────────────────────────

EC1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "total_cost_eur": 12.50}, 12.50),
    ({"ok": True, "total_cost_eur": 0.0}, 0.0),
    ({"ok": True, "total_cost_eur": None}, None),
    ({"ok": True}, None),
    ({}, None),
    (None, None),
])
EC2_attrs = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "period": "weekly", "avg_daily_cost_eur": 1.8, "total_consumption_kwh": 45.0, "total_savings_eur": 2.5, "days_count": 7}, "period", "weekly"),
    ({"ok": True, "period": "weekly", "avg_daily_cost_eur": 1.8, "total_consumption_kwh": 45.0, "total_savings_eur": 2.5, "days_count": 7}, "avg_daily_cost_eur", 1.8),
    ({"ok": True, "period": "weekly", "avg_daily_cost_eur": 1.8, "total_consumption_kwh": 45.0, "total_savings_eur": 2.5, "days_count": 7}, "total_consumption_kwh", 45.0),
    ({"ok": True, "period": "weekly", "avg_daily_cost_eur": 1.8, "total_consumption_kwh": 45.0, "total_savings_eur": 2.5, "days_count": 7}, "total_savings_eur", 2.5),
])
EC3_budget = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "budget_eur": 50.0, "spent_eur": 12.5, "remaining_eur": 37.5, "percent_used": 25.0, "on_track": True, "projected_total_eur": 45.0}, "budget_eur", 50.0),
    ({"ok": True, "budget_eur": 50.0, "spent_eur": 12.5, "remaining_eur": 37.5, "percent_used": 25.0, "on_track": True, "projected_total_eur": 45.0}, "budget_on_track", True),
    ({"ok": True, "budget_eur": 50.0, "spent_eur": 12.5, "remaining_eur": 37.5, "percent_used": 25.0, "on_track": True, "projected_total_eur": 45.0}, "budget_percent_used", 25.0),
    ({"ok": True, "budget_eur": 50.0, "spent_eur": 12.5, "remaining_eur": 37.5, "percent_used": 25.0, "on_track": True, "projected_total_eur": 45.0}, "budget_projected_eur", 45.0),
])


# ── EnergyForecastSensor test cases ─────────────────────────────────────────

EF1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "forecast_total_kwh": 12.5}, 12.5),
    ({"ok": True, "forecast_total_kwh": 0.0}, 0.0),
    ({"ok": True, "forecast_total_kwh": None}, None),
    ({}, None),
    ({"ok": True}, None),
])
EF2_attrs = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "date": "2026-04-05", "horizon_hours": 24, "forecast_cost_eur": 3.5, "confidence_pct": 87.5, "model_used": "lstm"}, "forecast_date", "2026-04-05"),
    ({"ok": True, "date": "2026-04-05", "horizon_hours": 24, "forecast_cost_eur": 3.5, "confidence_pct": 87.5, "model_used": "lstm"}, "horizon_hours", 24),
    ({"ok": True, "date": "2026-04-05", "horizon_hours": 24, "forecast_cost_eur": 3.5, "confidence_pct": 87.5, "model_used": "lstm"}, "forecast_cost_eur", 3.5),
    ({"ok": True, "date": "2026-04-05", "horizon_hours": 24, "forecast_cost_eur": 3.5, "confidence_pct": 87.5, "model_used": "lstm"}, "confidence_pct", 87.5),
    ({"ok": True, "date": "2026-04-05", "horizon_hours": 24, "forecast_cost_eur": 3.5, "confidence_pct": 87.5, "model_used": "lstm"}, "model_used", "lstm"),
])


# ── EnergyInsightsSensor test cases ─────────────────────────────────────────

EI1 = pytest.mark.parametrize("data,expected", [
    ({"ok": True, "insights": [{"id": 1}, {"id": 2}]}, 2),
    ({"ok": True, "insights": []}, 0),
    ({"ok": True, "insights": None}, 0),
    ({}, 0),
    ({"ok": True}, 0),
])
EI2_attrs = pytest.mark.parametrize("data,key,expected", [
    ({"ok": True, "insights": [{"type": "saving"}], "has_critical": False, "has_warnings": True}, "has_critical", False),
    ({"ok": True, "insights": [{"type": "saving"}], "has_critical": False, "has_warnings": True}, "has_warnings", True),
])


@EC1
def test_EC1_native_value(data, expected):
    s = EnergyCostSensorContract()
    s.apply_summary(data)
    assert s.native_value == expected


@EC2_attrs
def test_EC2_summary_attrs(data, key, expected):
    s = EnergyCostSensorContract()
    s.apply_summary(data)
    assert s.extra_state_attributes[key] == expected


@EC3_budget
def test_EC3_budget_attrs(data, key, expected):
    s = EnergyCostSensorContract()
    s.apply_budget(data)
    assert s.extra_state_attributes[key] == expected


@EF1
def test_EF1_native_value(data, expected):
    s = EnergyForecastSensorContract()
    s.apply(data)
    assert s.native_value == expected


@EF2_attrs
def test_EF2_attrs(data, key, expected):
    s = EnergyForecastSensorContract()
    s.apply(data)
    assert s.extra_state_attributes[key] == expected


@EI1
def test_EI1_native_value(data, expected):
    s = EnergyInsightsSensorContract()
    s.apply(data)
    assert s.native_value == expected


@EI2_attrs
def test_EI2_attrs(data, key, expected):
    s = EnergyInsightsSensorContract()
    s.apply(data)
    assert s.extra_state_attributes[key] == expected
