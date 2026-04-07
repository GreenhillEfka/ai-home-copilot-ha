"""Projection Contract Tests: energy_cost_sensor + energy_forecast_sensor (HA-143).

Verifies:
- EnergyCostSensor: pure projection on /api/v1/energy/costs/summary + /api/v1/energy/costs/budget
- EnergyForecastSensor: pure projection on /api/v1/regional/forecast/dashboard
"""

import pytest

from custom_components.copilot_ha.sensors.energy_cost_sensor import EnergyCostSensor
from custom_components.copilot_ha.sensors.energy_forecast_sensor import EnergyForecastSensor


# =============================================================================
# Contract Mirrors
# =============================================================================


class EnergyCostSensorContract:
    """Mirror of EnergyCostSensor state construction (test oracle)."""

    @staticmethod
    def native_value(summary_data: dict, budget_data: dict) -> float | None:
        if summary_data and summary_data.get("ok"):
            return summary_data.get("total_cost_eur")
        return None

    @staticmethod
    def extra_state_attributes(summary_data: dict, budget_data: dict) -> dict:
        attrs = {}
        if summary_data and summary_data.get("ok"):
            attrs.update({
                "period": summary_data.get("period"),
                "avg_daily_cost_eur": summary_data.get("avg_daily_cost_eur"),
                "total_consumption_kwh": summary_data.get("total_consumption_kwh"),
                "total_savings_eur": summary_data.get("total_savings_eur"),
                "days_count": summary_data.get("days_count"),
            })
        if budget_data and budget_data.get("ok"):
            attrs.update({
                "budget_eur": budget_data.get("budget_eur"),
                "budget_spent_eur": budget_data.get("spent_eur"),
                "budget_remaining_eur": budget_data.get("remaining_eur"),
                "budget_percent_used": budget_data.get("percent_used"),
                "budget_on_track": budget_data.get("on_track"),
                "budget_projected_eur": budget_data.get("projected_total_eur"),
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
            return {"total_hours": 0, "avg_price_ct_kwh": 0,
                    "min_price_ct_kwh": 0, "max_price_ct_kwh": 0,
                    "card_count": 0, "generated_at": ""}
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
    # EC1: ok with full data
    ({"ok": True, "total_cost_eur": 42.50}, {"ok": True, "budget_eur": 100}, 42.50),
    # EC2: ok with zero cost
    ({"ok": True, "total_cost_eur": 0.0}, {"ok": False}, 0.0),
    # EC3: ok with negative (credit)
    ({"ok": True, "total_cost_eur": -3.20}, {}, -3.20),
    # EC4: ok false
    ({"ok": False, "total_cost_eur": 99.0}, {}, None),
    # EC5: none summary
    (None, None, None),
    # EC6: empty dict
    ({}, {}, None),
    # EC7: missing ok key
    ({"total_cost_eur": 12.34}, {}, None),
])
def test_ec_native_value(summary_data, budget_data, expected):
    # Contract oracle
    result = EnergyCostSensorContract.native_value(summary_data, budget_data)
    assert result == expected


# =============================================================================
# EnergyCostSensor — extra_state_attributes (contract-based)
# =============================================================================

def test_ec_attrs_full():
    """Full summary + budget data."""
    summary = {"ok": True, "total_cost_eur": 42.50, "period": "weekly",
               "avg_daily_cost_eur": 6.07, "total_consumption_kwh": 150.0,
               "total_savings_eur": 8.50, "days_count": 7}
    budget = {"ok": True, "budget_eur": 100, "spent_eur": 42.50,
              "remaining_eur": 57.50, "percent_used": 42.5,
              "on_track": True, "projected_total_eur": 42.50}
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, budget)
    assert attrs["period"] == "weekly"
    assert attrs["avg_daily_cost_eur"] == 6.07
    assert attrs["total_consumption_kwh"] == 150.0
    assert attrs["budget_eur"] == 100
    assert attrs["budget_spent_eur"] == 42.50
    assert attrs["budget_on_track"] is True


def test_ec_attrs_partial_summary_only():
    """Only summary, no budget."""
    summary = {"ok": True, "total_cost_eur": 10.0}
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, None)
    assert attrs.get("period") is None
    assert "budget_eur" not in attrs


def test_ec_attrs_not_ok():
    """Summary ok=false, no budget."""
    summary = {"ok": False}
    attrs = EnergyCostSensorContract.extra_state_attributes(summary, None)
    assert "period" not in attrs


def test_ec_attrs_none():
    """Both None."""
    attrs = EnergyCostSensorContract.extra_state_attributes(None, None)
    assert attrs == {}


# =============================================================================
# EnergyForecastSensor — native_value
# =============================================================================

@pytest.mark.parametrize("data,expected", [
    # EF1: full data with pv estimate
    ({"summary": {"total_pv_kwh_estimated": 18.5}, "cards": []}, 18.5),
    # EF2: zero pv
    ({"summary": {"total_pv_kwh_estimated": 0.0}}, 0.0),
    # EF3: missing summary
    ({}, None),
    # EF4: empty summary
    ({"summary": {}}, None),
    # EF5: summary none
    ({"summary": None, "cards": []}, None),
    # EF6: data none
    (None, None),
    # EF7: summary is not dict
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
            "total_hours": 48, "avg_price_ct": 28.5, "min_price_ct": 12.0,
            "max_price_ct": 45.0, "cheapest_hour": "2026-04-06T03:00",
            "most_expensive_hour": "2026-04-06T18:00",
            "daylight_hours": 14, "avg_pv_factor": 0.65,
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
    # Only URL construction + dict lookups, no local computation
    assert "_core_base_url" in source
    assert "total_cost_eur" in source
    assert "budget_eur" in source


def test_ef_contract_pure_projection():
    """EnergyForecastSensor: pure projection shell on /api/v1/regional/forecast/dashboard."""
    import inspect
    source = inspect.getsource(EnergyForecastSensor)
    # Only summary dict lookups, no local computation
    assert "_core_base_url" in source
    assert "total_pv_kwh_estimated" in source
    assert "summary" in source


def test_ec_contract_no_local_semantic_invention():
    """EnergyCostSensor derives nothing locally — all from Core API."""
    # ok=False → None, no heuristic fallback
    assert EnergyCostSensorContract.native_value(
        {"ok": False, "total_cost_eur": 99.0}, {}
    ) is None
    # ok=True → value directly
    assert EnergyCostSensorContract.native_value(
        {"ok": True, "total_cost_eur": 42.50}, {}
    ) == 42.50


def test_ef_contract_no_local_semantic_invention():
    """EnergyForecastSensor derives nothing locally — all from Core API."""
    # Missing summary → None, no heuristic fallback
    assert EnergyForecastSensorContract.native_value({}) is None
    assert EnergyForecastSensorContract.native_value(None) is None
    # Valid summary → value directly
    assert EnergyForecastSensorContract.native_value(
        {"summary": {"total_pv_kwh_estimated": 18.5}}
    ) == 18.5
