"""Projection Contract Tests: tariff_sensor + energy_advisor_sensor (HA-131).

Verifies:
- TariffSensor: pure projection on /api/v1/regional/tariff/summary
- EnergyAdvisorSensor: pure projection on /api/v1/hub/energy
"""

import pytest


# =============================================================================
# Contract Mirrors
# =============================================================================


class TariffSensorContract:
    """Mirror of TariffSensor state construction."""

    @staticmethod
    def native_value(data: dict) -> float | None:
        return data.get("current_price_ct_kwh")

    @staticmethod
    def icon(data: dict) -> str:
        level = data.get("current_level", "normal")
        icons = {
            "very_low": "mdi:lightning-bolt",
            "low": "mdi:flash",
            "normal": "mdi:flash-outline",
            "high": "mdi:flash-alert",
            "very_high": "mdi:flash-alert-outline",
        }
        return icons.get(level, "mdi:flash-outline")

    @staticmethod
    def extra_state_attributes(data: dict) -> dict:
        return {
            "current_price_eur_kwh": data.get("current_price_eur_kwh"),
            "current_level": data.get("current_level", ""),
            "avg_price_ct_kwh": round((data.get("avg_price_eur_kwh") or 0) * 100, 2),
            "min_price_ct_kwh": round((data.get("min_price_eur_kwh") or 0) * 100, 2),
            "max_price_ct_kwh": round((data.get("max_price_eur_kwh") or 0) * 100, 2),
            "min_hour": data.get("min_hour", ""),
            "max_hour": data.get("max_hour", ""),
            "spread_ct_kwh": round((data.get("spread_eur_kwh") or 0) * 100, 2),
            "tariff_type": data.get("tariff_type", ""),
            "source": data.get("source", ""),
            "hours_available": data.get("hours_available", 0),
        }


class EnergyAdvisorSensorContract:
    """Mirror of EnergyAdvisorSensor state construction."""

    @staticmethod
    def native_value(data: dict) -> str:
        eco = data.get("eco_score", {})
        if not eco:
            return "Nicht verfügbar"
        grade = eco.get("grade", "?")
        score = eco.get("score", 0)
        return f"Eco-Score {grade} ({score}/100)"

    @staticmethod
    def icon(data: dict) -> str:
        eco = data.get("eco_score", {})
        grade = eco.get("grade", "C")
        icons = {
            "A+": "mdi:leaf",
            "A": "mdi:leaf",
            "B": "mdi:tree",
            "C": "mdi:flash",
            "D": "mdi:flash-alert",
            "E": "mdi:flash-alert-outline",
            "F": "mdi:lightning-bolt",
        }
        return icons.get(grade, "mdi:flash")

    @staticmethod
    def extra_state_attributes(data: dict) -> dict:
        eco = data.get("eco_score", {})
        attrs: dict = {
            "eco_score": eco.get("score", 0),
            "eco_grade": eco.get("grade", "?"),
            "eco_trend": eco.get("trend", "stabil"),
            "total_daily_kwh": data.get("total_daily_kwh", 0),
            "total_monthly_kwh": data.get("total_monthly_kwh", 0),
            "total_monthly_eur": data.get("total_monthly_eur", 0),
            "savings_potential_eur": data.get("savings_potential_eur", 0),
        }
        breakdown = data.get("breakdown", [])
        if breakdown:
            attrs["breakdown"] = [
                {"category": b.get("name_de"), "kwh": b.get("kwh"), "pct": b.get("pct")}
                for b in breakdown
            ]
        top = data.get("top_consumers", [])
        if top:
            attrs["top_consumers"] = [
                {"name": c.get("name"), "monthly_kwh": c.get("monthly_kwh")}
                for c in top[:5]
            ]
        recs = data.get("recommendations", [])
        if recs:
            attrs["recommendations"] = [
                {
                    "title": r.get("title_de"),
                    "savings_eur": r.get("potential_savings_eur"),
                    "difficulty": r.get("difficulty"),
                    "applied": r.get("applied"),
                }
                for r in recs[:5]
            ]
        return attrs


# =============================================================================
# TariffSensor Tests — TS1: native_value
# =============================================================================


@pytest.mark.parametrize("data,expected", [
    ({"current_price_ct_kwh": 28.5, "ok": True}, 28.5),
    ({"current_price_ct_kwh": 12.3, "ok": True}, 12.3),
    ({"current_price_ct_kwh": 0.0, "ok": True}, 0.0),
    ({"current_price_ct_kwh": None, "ok": True}, None),
    ({"ok": True}, None),
])
def test_tariff_sensor_native_value(data, expected):
    assert TariffSensorContract.native_value(data) == expected


# TS2: icon


@pytest.mark.parametrize("level,expected", [
    ("very_low", "mdi:lightning-bolt"),
    ("low", "mdi:flash"),
    ("normal", "mdi:flash-outline"),
    ("high", "mdi:flash-alert"),
    ("very_high", "mdi:flash-alert-outline"),
    ("unknown_level", "mdi:flash-outline"),
    ("", "mdi:flash-outline"),
])
def test_tariff_sensor_icon(level, expected):
    data = {"current_level": level, "ok": True}
    assert TariffSensorContract.icon(data) == expected


# TS3: extra_state_attributes


def test_tariff_sensor_attrs_full():
    data = {
        "current_price_eur_kwh": 0.285,
        "current_level": "high",
        "avg_price_eur_kwh": 0.260,
        "min_price_eur_kwh": 0.180,
        "max_price_eur_kwh": 0.350,
        "min_hour": "03:00",
        "max_hour": "20:00",
        "spread_eur_kwh": 0.170,
        "tariff_type": "aWATTar",
        "source": "EPEX",
        "hours_available": 24,
        "ok": True,
    }
    attrs = TariffSensorContract.extra_state_attributes(data)
    assert attrs["current_price_eur_kwh"] == 0.285
    assert attrs["current_level"] == "high"
    assert attrs["avg_price_ct_kwh"] == 26.0
    assert attrs["min_price_ct_kwh"] == 18.0
    assert attrs["max_price_ct_kwh"] == 35.0
    assert attrs["min_hour"] == "03:00"
    assert attrs["max_hour"] == "20:00"
    assert attrs["spread_ct_kwh"] == 17.0
    assert attrs["tariff_type"] == "aWATTar"
    assert attrs["source"] == "EPEX"
    assert attrs["hours_available"] == 24


def test_tariff_sensor_attrs_missing_optionals():
    data = {"ok": True}
    attrs = TariffSensorContract.extra_state_attributes(data)
    assert attrs["current_price_eur_kwh"] is None
    assert attrs["current_level"] == ""
    assert attrs["avg_price_ct_kwh"] == 0.0
    assert attrs["min_price_ct_kwh"] == 0.0
    assert attrs["max_price_ct_kwh"] == 0.0
    assert attrs["min_hour"] == ""
    assert attrs["max_hour"] == ""
    assert attrs["spread_ct_kwh"] == 0.0
    assert attrs["tariff_type"] == ""
    assert attrs["source"] == ""
    assert attrs["hours_available"] == 0


def test_tariff_sensor_attrs_zero_spread():
    data = {"spread_eur_kwh": 0.0, "ok": True}
    attrs = TariffSensorContract.extra_state_attributes(data)
    assert attrs["spread_ct_kwh"] == 0.0


# =============================================================================
# EnergyAdvisorSensor Tests — EA1: native_value
# =============================================================================


@pytest.mark.parametrize("data,expected", [
    ({"eco_score": {"grade": "A", "score": 92}, "ok": True}, "Eco-Score A (92/100)"),
    ({"eco_score": {"grade": "C", "score": 55}, "ok": True}, "Eco-Score C (55/100)"),
    ({"eco_score": {"grade": "F", "score": 10}, "ok": True}, "Eco-Score F (10/100)"),
    ({"eco_score": {}, "ok": True}, "Nicht verfügbar"),
    ({"ok": True}, "Nicht verfügbar"),
    ({"eco_score": {"score": 0}, "ok": True}, "Eco-Score ? (0/100)"),
])
def test_energy_advisor_native_value(data, expected):
    assert EnergyAdvisorSensorContract.native_value(data) == expected


# EA2: icon


@pytest.mark.parametrize("grade,expected", [
    ("A+", "mdi:leaf"),
    ("A", "mdi:leaf"),
    ("B", "mdi:tree"),
    ("C", "mdi:flash"),
    ("D", "mdi:flash-alert"),
    ("E", "mdi:flash-alert-outline"),
    ("F", "mdi:lightning-bolt"),
    ("X", "mdi:flash"),
    ("", "mdi:flash"),
])
def test_energy_advisor_icon(grade, expected):
    data = {"eco_score": {"grade": grade}, "ok": True}
    assert EnergyAdvisorSensorContract.icon(data) == expected


# EA3: extra_state_attributes


def test_energy_advisor_attrs_full():
    data = {
        "eco_score": {"grade": "B", "score": 71, "trend": "steigend"},
        "total_daily_kwh": 12.5,
        "total_monthly_kwh": 375.0,
        "total_monthly_eur": 112.50,
        "savings_potential_eur": 28.0,
        "breakdown": [
            {"name_de": "Heizung", "kwh": 150.0, "pct": 40},
            {"name_de": "Beleuchtung", "kwh": 75.0, "pct": 20},
        ],
        "top_consumers": [
            {"name": "Wärmepumpe", "monthly_kwh": 200.0},
            {"name": "E-Auto", "monthly_kwh": 120.0},
        ],
        "recommendations": [
            {"title_de": "LED tauschen", "potential_savings_eur": 15.0, "difficulty": "einfach", "applied": False},
        ],
        "ok": True,
    }
    attrs = EnergyAdvisorSensorContract.extra_state_attributes(data)
    assert attrs["eco_score"] == 71
    assert attrs["eco_grade"] == "B"
    assert attrs["eco_trend"] == "steigend"
    assert attrs["total_daily_kwh"] == 12.5
    assert attrs["total_monthly_kwh"] == 375.0
    assert attrs["total_monthly_eur"] == 112.50
    assert attrs["savings_potential_eur"] == 28.0
    assert len(attrs["breakdown"]) == 2
    assert attrs["breakdown"][0]["category"] == "Heizung"
    assert len(attrs["top_consumers"]) == 2
    assert len(attrs["recommendations"]) == 1
    assert attrs["recommendations"][0]["title"] == "LED tauschen"


def test_energy_advisor_attrs_missing_optionals():
    data = {"ok": True}
    attrs = EnergyAdvisorSensorContract.extra_state_attributes(data)
    assert attrs["eco_score"] == 0
    assert attrs["eco_grade"] == "?"
    assert attrs["eco_trend"] == "stabil"
    assert attrs["total_daily_kwh"] == 0
    assert attrs["total_monthly_kwh"] == 0
    assert attrs["total_monthly_eur"] == 0
    assert attrs["savings_potential_eur"] == 0
    assert "breakdown" not in attrs
    assert "top_consumers" not in attrs
    assert "recommendations" not in attrs


def test_energy_advisor_attrs_empty_lists():
    data = {"eco_score": {"grade": "C", "score": 50}, "breakdown": [], "top_consumers": [], "recommendations": [], "ok": True}
    attrs = EnergyAdvisorSensorContract.extra_state_attributes(data)
    assert "breakdown" not in attrs
    assert "top_consumers" not in attrs
    assert "recommendations" not in attrs


def test_energy_advisor_attrs_top_consumers_capped():
    data = {
        "eco_score": {"grade": "A", "score": 88},
        "top_consumers": [
            {"name": f"Gerät {i}", "monthly_kwh": 10.0 * i}
            for i in range(10)
        ],
        "ok": True,
    }
    attrs = EnergyAdvisorSensorContract.extra_state_attributes(data)
    assert len(attrs["top_consumers"]) == 5  # capped at 5


def test_energy_advisor_attrs_recommendations_capped():
    data = {
        "eco_score": {"grade": "B", "score": 65},
        "recommendations": [
            {"title_de": f"Tipp {i}", "potential_savings_eur": i * 5.0, "difficulty": "mittel", "applied": False}
            for i in range(10)
        ],
        "ok": True,
    }
    attrs = EnergyAdvisorSensorContract.extra_state_attributes(data)
    assert len(attrs["recommendations"]) == 5  # capped at 5


# =============================================================================
# Global Contract Tests
# =============================================================================


def test_tariff_sensor_global_contract():
    """TariffSensor hits /api/v1/regional/tariff/summary — pure projection, no local semantic invention."""
    # Contract: native_value is direct lookup, icon is level→icon map, attrs are unit conversions
    data = {"current_price_ct_kwh": 31.2, "current_level": "normal", "ok": True}
    assert TariffSensorContract.native_value(data) == 31.2
    assert TariffSensorContract.icon(data) == "mdi:flash-outline"
    # No local heuristics: min/max/spread are server-computed, sensor just converts units


def test_energy_advisor_global_contract():
    """EnergyAdvisorSensor hits /api/v1/hub/energy — pure projection, no local semantic invention."""
    # Contract: eco_score is server-computed, sensor formats grade+score as string
    data = {"eco_score": {"grade": "A", "score": 95}, "ok": True}
    assert EnergyAdvisorSensorContract.native_value(data) == "Eco-Score A (95/100)"
    assert EnergyAdvisorSensorContract.icon(data) == "mdi:leaf"
    # No local classification: grade is server-provided
