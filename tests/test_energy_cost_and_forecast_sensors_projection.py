"""Projection Contract Tests: energy_cost_sensor + energy_forecast_sensor (HA-326).

Verifies:
- EnergyCostSensor: pure projection on /api/v1/energy/costs/summary + /api/v1/energy/costs/budget
- EnergyForecastSensor: pure projection on /api/v1/regional/forecast/dashboard
"""

import math

import pytest

from custom_components.pilotsuite.sensors.energy_cost_sensor import EnergyCostSensor
from custom_components.pilotsuite.sensors.energy_forecast_sensor import EnergyForecastSensor


# =============================================================================
# Contract Mirrors
# =============================================================================


def _as_mapping(value):
    if isinstance(value, dict):
        return value
    return {}


def _as_float(value, default):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return default


def _as_int(value, default):
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value == int(value):
        return int(value)
    return default


def _as_string(value, default):
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _as_bool(value, default):
    if isinstance(value, bool):
        return value
    return default


class EnergyCostSensorContract:
    """Mirror of EnergyCostSensor state construction (test oracle)."""

    @staticmethod
    def native_value(summary_data: dict, budget_data: dict) -> float | None:
        summary = _as_mapping(summary_data)
        if summary and summary.get("ok"):
            return _as_float(summary.get("total_cost_eur"), None)
        return None

    @staticmethod
    def extra_state_attributes(summary_data: dict, budget_data: dict) -> dict:
        attrs = {}
        summary = _as_mapping(summary_data)
        if summary and summary.get("ok"):
            attrs.update({
                "period": _as_string(summary.get("period"), None),
                "avg_daily_cost_eur": _as_float(summary.get("avg_daily_cost_eur"), 0.0),
                "total_consumption_kwh": _as_float(summary.get("total_consumption_kwh"), 0.0),
                "total_savings_eur": _as_float(summary.get("total_savings_eur"), 0.0),
                "days_count": _as_int(summary.get("days_count"), 0),
            })
        budget = _as_mapping(budget_data)
        if budget and budget.get("ok"):
            attrs.update({
                "budget_eur": _as_float(budget.get("budget_eur"), 0.0),
                "budget_spent_eur": _as_float(budget.get("spent_eur"), 0.0),
                "budget_remaining_eur": _as_float(budget.get("remaining_eur"), 0.0),
                "budget_percent_used": _as_float(budget.get("percent_used"), 0.0),
                "budget_on_track": _as_bool(budget.get("on_track"), False),
                "budget_projected_eur": _as_float(budget.get("projected_total_eur"), 0.0),
            })
        return attrs


class EnergyForecastSensorContract:
    """Mirror of EnergyForecastSensor state construction (test oracle)."""

    @staticmethod
    def native_value(data: dict) -> float | None:
        summary = data.get("summary") if data else None
        if isinstance(summary, dict):
            return summary.get("total_pv_kwh_estimated")
        return None

    @staticmethod
    def extra_state_attributes(data: dict) -> dict:
        if not data:
            return {
                "total_hours": 0,
                "avg_price_ct_kwh": 0,
                "min_price_ct_kwh": 0,
                "max_price_ct_kwh": 0,
                "card_count": 0,
                "generated_at": "",
            }
        summary = data.get("summary", {})
        cards = data.get("cards", [])
        return {
            "total_hours": summary.get("total_hours", 0) if isinstance(summary, dict) else 0,
            "avg_price_ct_kwh": summary.get("avg_price_ct", 0) if isinstance(summary, dict) else 0,
            "min_price_ct_kwh": summary.get("min_price_ct", 0) if isinstance(summary, dict) else 0,
            "max_price_ct_kwh": summary.get("max_price_ct", 0) if isinstance(summary, dict) else 0,
            "cheapest_hour": summary.get("cheapest_hour", "") if isinstance(summary, dict) else "",
            "most_expensive_hour": summary.get("most_expensive_hour", "") if isinstance(summary, dict) else "",
            "daylight_hours": summary.get("daylight_hours", 0) if isinstance(summary, dict) else 0,
            "avg_pv_factor": summary.get("avg_pv_factor", 0) if isinstance(summary, dict) else 0,
            "best_charge_window": summary.get("best_charge_window", "") if isinstance(summary, dict) else "",
            "best_consume_window": summary.get("best_consume_window", "") if isinstance(summary, dict) else "",
            "weather_impacted_hours": summary.get("weather_impacted_hours", 0) if isinstance(summary, dict) else 0,
            "card_count": len(cards) if isinstance(cards, list) else 0,
            "generated_at": data.get("generated_at", "") or "",
        }


# =============================================================================
# EnergyCostSensor — native_value
# =============================================================================

@pytest.mark.parametrize("summary_data,budget_data,expected", [
    ({"ok": True, "total_cost_eur": 42.50}, {"ok": True, "budget_eur": 100}, 42.50),
    ({"ok": True, "total_cost_eur": 0.0}, {"ok": False}, 0.0),
    ({"ok": True, "total_cost_eur": -3.20}, {}, -3.20),
    ({"ok": False, "total_cost_eur": 99.0}, {}, None),
    (None, None, None),
    ({}, {}, None),
    ({"total_cost_eur": 12.34}, {}, None),
    ("not-a-dict", None, None),
    ([{"ok": True}], None, None),
    (42, None, None),
    (True, None, None),
    ({"ok": True, "total_cost_eur": "expensive"}, None, None),
    ({"ok": True, "total_cost_eur": True}, None, None),
    ({"ok": True, "total_cost_eur": None}, None, None),
    ({"ok": True, "total_cost_eur": float("inf")}, None, None),
    ({"ok": True, "total_cost_eur": float("nan")}, None, None),
])
def test_ec_native_value(summary_data, budget_data, expected):
    result = EnergyCostSensorContract.native_value(summary_data, budget_data)
    if isinstance(expected, float) and math.isnan(expected):
        assert math.isnan(result)
    else:
        assert result == expected


# =============================================================================
# EnergyCostSensor — extra_state_attributes
# =============================================================================

def test_ec_attrs_full():
    summary = {
        "ok": True,
        "total_cost_eur": 42.50,
        "period": "weekly",
        "avg_daily_cost_eur": 6.07,
        "total_consumption_kwh": 150.0,
        "total_savings_eur": 8.50,
        "days_count": 7,
    }
    budget = {
        "ok": True,
        "budget_eur": 100,
        "spent_eur": 42.50,
        "remaining_eur": 57.50,
        "percent_used": 42.5,
        "on_track": True,
        "projected_total_eur": 42.50,
    }
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, budget)
    assert attrs["period"] == "weekly"
    assert attrs["avg_daily_cost_eur"] == 6.07
    assert attrs["total_consumption_kwh"] == 150.0
    assert attrs["budget_eur"] == 100
    assert attrs["budget_spent_eur"] == 42.50
    assert attrs["budget_on_track"] is True


def test_ec_attrs_partial_summary_only():
    summary = {"ok": True, "total_cost_eur": 10.0}
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, None)
    assert attrs.get("period") is None
    assert "budget_eur" not in attrs


def test_ec_attrs_not_ok():
    summary = {"ok": False}
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, None)
    assert "period" not in attrs


def test_ec_attrs_none():
    attrs = EnergyCostSensorContract.extra_state_attributes(None, None)
    assert attrs == {}


def test_ec_attrs_malformed_summary_type():
    attrs = EnergyCostSensorContract.extra_state_attributes("string-summary", {})
    assert "period" not in attrs

    attrs = EnergyCostSensorContract.extra_state_attributes([], {})
    assert "period" not in attrs

    attrs = EnergyCostSensorContract.extra_state_attributes(42, {})
    assert "period" not in attrs


def test_ec_attrs_malformed_budget_type():
    summary = {
        "ok": True,
        "total_cost_eur": 42.50,
        "period": "weekly",
        "avg_daily_cost_eur": 6.07,
        "total_consumption_kwh": 150.0,
        "total_savings_eur": 8.50,
        "days_count": 7,
    }
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, "not-a-dict")
    assert attrs["period"] == "weekly"
    assert "budget_eur" not in attrs


def test_ec_attrs_malformed_summary_fields():
    summary = {
        "ok": True,
        "total_cost_eur": 42.50,
        "period": "   ",
        "avg_daily_cost_eur": "expensive",
        "total_consumption_kwh": None,
        "total_savings_eur": True,
        "days_count": "seven",
    }
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, None)
    assert attrs["period"] is None
    assert attrs["avg_daily_cost_eur"] == 0.0
    assert attrs["total_consumption_kwh"] == 0.0
    assert attrs["total_savings_eur"] == 0.0
    assert attrs["days_count"] == 0


def test_ec_attrs_malformed_budget_fields():
    budget = {
        "ok": True,
        "budget_eur": "hundred",
        "spent_eur": None,
        "remaining_eur": False,
        "percent_used": [],
        "on_track": "yes",
        "projected_total_eur": {},
    }
    attrs = EnergyCostSensorContract.extra_state_attributes(None, budget)
    assert attrs["budget_eur"] == 0.0
    assert attrs["budget_spent_eur"] == 0.0
    assert attrs["budget_remaining_eur"] == 0.0
    assert attrs["budget_percent_used"] == 0.0
    assert attrs["budget_on_track"] is False
    assert attrs["budget_projected_eur"] == 0.0


# =============================================================================
# EnergyForecastSensor — native_value
# =============================================================================

@pytest.mark.parametrize("data,expected", [
    ({"summary": {"total_pv_kwh_estimated": 18.5}, "cards": []}, 18.5),
    ({"summary": {"total_pv_kwh_estimated": 0.0}}, 0.0),
    ({}, None),
    ({"summary": {}}, None),
    ({"summary": None, "cards": []}, None),
    (None, None),
    ({"summary": "not-a-dict"}, None),
])
def test_ef_native_value(data, expected):
    result = EnergyForecastSensorContract.native_value(data)
    assert result == expected


# =============================================================================
# EnergyForecastSensor — extra_state_attributes
# =============================================================================

def test_ef_attrs_full():
    data = {
        "summary": {
            "total_hours": 48,
            "avg_price_ct": 28.5,
            "min_price_ct": 12.0,
            "max_price_ct": 45.0,
            "cheapest_hour": "2026-04-06T03:00",
            "most_expensive_hour": "2026-04-06T18:00",
            "daylight_hours": 14,
            "avg_pv_factor": 0.65,
            "best_charge_window": "2026-04-06T14:00",
            "best_consume_window": "2026-04-06T12:00",
            "weather_impacted_hours": 3,
        },
        "cards": [{}, {}, {}],
        "generated_at": "2026-04-06T10:00:00Z",
    }
    attrs = EnergyForecastSensorContract.extra_state_attributes(data)
    assert attrs["total_hours"] == 48
    assert attrs["avg_price_ct_kwh"] == 28.5
    assert attrs["min_price_ct_kwh"] == 12.0
    assert attrs["max_price_ct_kwh"] == 45.0
    assert attrs["cheapest_hour"] == "2026-04-06T03:00"
    assert attrs["daylight_hours"] == 14
    assert attrs["avg_pv_factor"] == 0.65
    assert attrs["card_count"] == 3
    assert attrs["generated_at"] == "2026-04-06T10:00:00Z"


def test_ef_attrs_empty():
    attrs = EnergyForecastSensorContract.extra_state_attributes({})
    assert attrs["total_hours"] == 0
    assert attrs["avg_price_ct_kwh"] == 0
    assert attrs["card_count"] == 0
    assert attrs["generated_at"] == ""


def test_ef_attrs_none():
    attrs = EnergyForecastSensorContract.extra_state_attributes(None)
    assert attrs["total_hours"] == 0
    assert attrs["card_count"] == 0


# =============================================================================
# Global Contract
# =============================================================================

def test_ec_contract_pure_projection():
    """EnergyCostSensor: pure projection shell on /api/v1/energy/costs/*."""
    import inspect

    source = inspect.getsource(EnergyCostSensor)
    assert "_core_base_url" in source
    assert "total_cost_eur" in source
    assert "budget_eur" in source


def test_ef_contract_pure_projection():
    """EnergyForecastSensor: pure projection shell on /api/v1/regional/forecast/dashboard."""
    import inspect

    source = inspect.getsource(EnergyForecastSensor)
    assert "_core_base_url" in source
    assert "total_pv_kwh_estimated" in source
    assert "summary" in source


def test_ec_contract_no_local_semantic_invention():
    """EnergyCostSensor derives nothing locally, all from Core API."""
    assert EnergyCostSensorContract.native_value(
        {"ok": False, "total_cost_eur": 99.0}, {}
    ) is None
    assert EnergyCostSensorContract.native_value(
        {"ok": True, "total_cost_eur": 42.50}, {}
    ) == 42.50


def test_ef_contract_no_local_semantic_invention():
    """EnergyForecastSensor derives nothing locally, all from Core API."""
    assert EnergyForecastSensorContract.native_value({}) is None
    assert EnergyForecastSensorContract.native_value(None) is None
    assert EnergyForecastSensorContract.native_value(
        {"summary": {"total_pv_kwh_estimated": 18.5}}
    ) == 18.5


# =============================================================================
# Source Guard — energy_cost hardening present in production
# =============================================================================

def test_ec_source_guard_helpers_present():
    import inspect

    source = inspect.getsource(EnergyCostSensor)
    assert "_as_mapping" in source
    assert "_as_float" in source
    assert "_as_int" in source
    assert "_as_string" in source
    assert "_as_bool" in source


def test_ec_source_guard_async_update_normalizes_payloads():
    import inspect

    source = inspect.getsource(EnergyCostSensor)
    assert "self._summary_data = _as_mapping(data)" in source
    assert "self._budget_data = _as_mapping(data)" in source
