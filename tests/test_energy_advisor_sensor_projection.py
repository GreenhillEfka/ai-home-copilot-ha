"""Projection contract tests for energy_advisor_sensor.py.

Verifies EnergyAdvisorSensor is a pure projection shell on
`/api/v1/hub/energy` data with only trivial formatting and list trimming.

HA-254 / HA-329
"""

from __future__ import annotations

import asyncio
import math

import pytest

from custom_components.pilotsuite.sensors.energy_advisor_sensor import (
    EnergyAdvisorSensor,
    _as_float,
    _as_int,
    _as_list,
    _as_mapping,
    _as_string,
)


class EnergyAdvisorSensorContract:
    """Mirror of EnergyAdvisorSensor projection logic with guard semantics (HA-329)."""

    _GRADE_ICONS = {
        "A+": "mdi:leaf",
        "A": "mdi:leaf",
        "B": "mdi:tree",
        "C": "mdi:flash",
        "D": "mdi:flash-alert",
        "E": "mdi:flash-alert-outline",
        "F": "mdi:lightning-bolt",
    }

    @staticmethod
    def native_value(data: dict) -> str:
        d = _as_mapping(data)
        eco = _as_mapping(d.get("eco_score"))
        grade = _as_string(eco.get("grade"), "?")
        score = _as_int(eco.get("score"), 0)
        if not eco:
            return "Nicht verfügbar"
        return f"Eco-Score {grade} ({score}/100)"

    @staticmethod
    def icon(data: dict) -> str:
        d = _as_mapping(data)
        eco = _as_mapping(d.get("eco_score"))
        grade = _as_string(eco.get("grade"), "C")
        return EnergyAdvisorSensorContract._GRADE_ICONS.get(grade, "mdi:flash")

    @staticmethod
    def attrs(data: dict) -> dict:
        d = _as_mapping(data)
        eco = _as_mapping(d.get("eco_score"))
        attrs = {
            "eco_score": _as_int(eco.get("score"), 0),
            "eco_grade": _as_string(eco.get("grade"), "?"),
            "eco_trend": _as_string(eco.get("trend"), "stabil"),
            "total_daily_kwh": _as_float(d.get("total_daily_kwh"), 0.0),
            "total_monthly_kwh": _as_float(d.get("total_monthly_kwh"), 0.0),
            "total_monthly_eur": _as_float(d.get("total_monthly_eur"), 0.0),
            "savings_potential_eur": _as_float(d.get("savings_potential_eur"), 0.0),
        }

        breakdown = _as_list(d.get("breakdown"))
        if breakdown:
            attrs["breakdown"] = [
                {
                    "category": _as_string(_as_mapping(b).get("name_de"), ""),
                    "kwh": _as_float(_as_mapping(b).get("kwh"), 0.0),
                    "pct": _as_float(_as_mapping(b).get("pct"), 0.0),
                }
                for b in breakdown
                if isinstance(b, dict)
            ]

        top = _as_list(d.get("top_consumers"))
        if top:
            attrs["top_consumers"] = [
                {
                    "name": _as_string(_as_mapping(c).get("name"), ""),
                    "monthly_kwh": _as_float(_as_mapping(c).get("monthly_kwh"), 0.0),
                }
                for c in top[:5]
                if isinstance(c, dict)
            ]

        recs = _as_list(d.get("recommendations"))
        if recs:
            attrs["recommendations"] = [
                {
                    "title": _as_string(_as_mapping(r).get("title_de"), ""),
                    "savings_eur": _as_float(_as_mapping(r).get("potential_savings_eur"), 0.0),
                    "difficulty": _as_string(_as_mapping(r).get("difficulty"), ""),
                    "applied": _as_mapping(r).get("applied"),
                }
                for r in recs[:5]
                if isinstance(r, dict)
            ]

        return attrs


class FakeCoordinator:
    def __init__(self) -> None:
        self._config = {}
        self.data = {}


def _make_sensor(data: dict | None = None) -> EnergyAdvisorSensor:
    sensor = EnergyAdvisorSensor(FakeCoordinator())
    sensor._data = _as_mapping(data)
    return sensor


# ---------------------------------------------------------------------------
# Native value
# ---------------------------------------------------------------------------

class TestEnergyAdvisorNativeValue:
    def test_ea1_native_value_full_projection(self):
        data = {"eco_score": {"grade": "A", "score": 92}}
        sensor = _make_sensor(data)
        assert sensor.native_value == "Eco-Score A (92/100)"

    def test_ea2_native_value_defaults_to_not_available_without_eco_score(self):
        sensor = _make_sensor({})
        assert sensor.native_value == "Nicht verfügbar"

    def test_ea3_native_value_keeps_zero_score(self):
        data = {"eco_score": {"grade": "F", "score": 0}}
        sensor = _make_sensor(data)
        assert sensor.native_value == "Eco-Score F (0/100)"

    def test_ea4_native_value_uses_fallbacks_without_local_inference(self):
        data = {"eco_score": {"trend": "fallend"}}
        sensor = _make_sensor(data)
        assert sensor.native_value == "Eco-Score ? (0/100)"

    # HA-329 malformed cases
    def test_ea10_native_value_non_dict_eco_score_returns_not_available(self):
        sensor = _make_sensor({"eco_score": "broken"})
        assert sensor.native_value == "Nicht verfügbar"

    def test_ea11_native_value_non_numeric_score_defaults_to_zero(self):
        sensor = _make_sensor({"eco_score": {"grade": "A", "score": "twenty"}})
        assert sensor.native_value == "Eco-Score A (0/100)"

    def test_ea12_native_value_inf_score_defaults_to_zero(self):
        sensor = _make_sensor({"eco_score": {"grade": "A", "score": float("inf")}})
        assert sensor.native_value == "Eco-Score A (0/100)"

    def test_ea13_native_value_nan_score_defaults_to_zero(self):
        sensor = _make_sensor({"eco_score": {"grade": "A", "score": float("nan")}})
        assert sensor.native_value == "Eco-Score A (0/100)"

    def test_ea14_native_value_bool_score_defaults_to_zero(self):
        sensor = _make_sensor({"eco_score": {"grade": "B", "score": True}})
        assert sensor.native_value == "Eco-Score B (0/100)"


# ---------------------------------------------------------------------------
# Icon
# ---------------------------------------------------------------------------

class TestEnergyAdvisorIcon:
    @pytest.mark.parametrize(
        ("grade", "expected_icon"),
        [
            ("A+", "mdi:leaf"),
            ("A", "mdi:leaf"),
            ("B", "mdi:tree"),
            ("C", "mdi:flash"),
            ("D", "mdi:flash-alert"),
            ("E", "mdi:flash-alert-outline"),
            ("F", "mdi:lightning-bolt"),
            ("unknown", "mdi:flash"),
        ],
    )
    def test_ei1_to_ei8_grade_icon_mapping(self, grade: str, expected_icon: str):
        sensor = _make_sensor({"eco_score": {"grade": grade}})
        assert sensor.icon == expected_icon

    def test_ei9_missing_grade_defaults_to_c_flash_icon(self):
        sensor = _make_sensor({"eco_score": {}})
        assert sensor.icon == "mdi:flash"

    # HA-329 malformed cases
    def test_ei10_icon_non_dict_eco_score_defaults_to_c_flash(self):
        sensor = _make_sensor({"eco_score": ["list", "not", "dict"]})
        assert sensor.icon == "mdi:flash"

    def test_ei11_icon_blank_grade_defaults_to_c_flash(self):
        sensor = _make_sensor({"eco_score": {"grade": "   "}})
        assert sensor.icon == "mdi:flash"


# ---------------------------------------------------------------------------
# Extra state attributes
# ---------------------------------------------------------------------------

class TestEnergyAdvisorAttrs:
    def test_ea5_attrs_defaults_when_empty(self):
        sensor = _make_sensor({})
        assert sensor.extra_state_attributes == {
            "eco_score": 0,
            "eco_grade": "?",
            "eco_trend": "stabil",
            "total_daily_kwh": 0.0,
            "total_monthly_kwh": 0.0,
            "total_monthly_eur": 0.0,
            "savings_potential_eur": 0.0,
        }

    def test_ea6_attrs_full_passthrough_and_projection(self):
        data = {
            "eco_score": {"grade": "B", "score": 81, "trend": "fallend"},
            "total_daily_kwh": 14.2,
            "total_monthly_kwh": 402.7,
            "total_monthly_eur": 118.4,
            "savings_potential_eur": 21.9,
            "breakdown": [
                {"name_de": "Heizung", "kwh": 120.0, "pct": 35},
                {"name_de": "Licht", "kwh": 42.5, "pct": 12},
            ],
            "top_consumers": [
                {"name": f"consumer-{i}", "monthly_kwh": i * 10, "ignored": True}
                for i in range(7)
            ],
            "recommendations": [
                {
                    "title_de": f"Tipp {i}",
                    "potential_savings_eur": i * 2.5,
                    "difficulty": "easy" if i % 2 == 0 else "medium",
                    "applied": i % 2 == 0,
                    "ignored": "drop-me",
                }
                for i in range(7)
            ],
        }
        sensor = _make_sensor(data)
        attrs = sensor.extra_state_attributes

        assert attrs["eco_score"] == 81
        assert attrs["eco_grade"] == "B"
        assert attrs["eco_trend"] == "fallend"
        assert attrs["total_daily_kwh"] == 14.2
        assert attrs["total_monthly_kwh"] == 402.7
        assert attrs["total_monthly_eur"] == 118.4
        assert attrs["savings_potential_eur"] == 21.9
        assert attrs["breakdown"] == [
            {"category": "Heizung", "kwh": 120.0, "pct": 35},
            {"category": "Licht", "kwh": 42.5, "pct": 12},
        ]
        assert len(attrs["top_consumers"]) == 5
        assert attrs["top_consumers"][0] == {"name": "consumer-0", "monthly_kwh": 0.0}
        assert attrs["top_consumers"][-1] == {"name": "consumer-4", "monthly_kwh": 40.0}
        assert len(attrs["recommendations"]) == 5
        assert attrs["recommendations"][0] == {
            "title": "Tipp 0",
            "savings_eur": 0.0,
            "difficulty": "easy",
            "applied": True,
        }
        assert attrs["recommendations"][-1] == {
            "title": "Tipp 4",
            "savings_eur": 10.0,
            "difficulty": "easy",
            "applied": True,
        }

    def test_ea7_attrs_omit_optional_lists_when_empty(self):
        sensor = _make_sensor(
            {
                "eco_score": {"grade": "A", "score": 95},
                "breakdown": [],
                "top_consumers": [],
                "recommendations": [],
            }
        )
        attrs = sensor.extra_state_attributes
        assert "breakdown" not in attrs
        assert "top_consumers" not in attrs
        assert "recommendations" not in attrs

    # HA-329: malformed payloads now normalised to safe defaults
    def test_ea15_attrs_non_dict_eco_score_normalised_to_defaults(self):
        sensor = _make_sensor({"eco_score": "string"})
        assert sensor.extra_state_attributes["eco_score"] == 0
        assert sensor.extra_state_attributes["eco_grade"] == "?"

    def test_ea16_attrs_non_numeric_kwh_normalised_to_zero(self):
        sensor = _make_sensor({"total_daily_kwh": "14.2wh", "total_monthly_kwh": None})
        attrs = sensor.extra_state_attributes
        assert attrs["total_daily_kwh"] == 0.0
        assert attrs["total_monthly_kwh"] == 0.0

    def test_ea17_attrs_inf_kwh_normalised_to_zero(self):
        sensor = _make_sensor({"total_monthly_kwh": float("inf"), "total_monthly_eur": float("nan")})
        attrs = sensor.extra_state_attributes
        assert attrs["total_monthly_kwh"] == 0.0
        assert attrs["total_monthly_eur"] == 0.0

    def test_ea18_attrs_bool_kwh_normalised_to_zero(self):
        sensor = _make_sensor({"total_daily_kwh": True})
        assert sensor.extra_state_attributes["total_daily_kwh"] == 0.0

    def test_ea19_attrs_non_dict_breakdown_items_skipped(self):
        sensor = _make_sensor({"breakdown": ["not a dict", 42, None, {"name_de": "Valid"}]})
        attrs = sensor.extra_state_attributes
        assert attrs["breakdown"] == [{"category": "Valid", "kwh": 0.0, "pct": 0.0}]

    def test_ea20_attrs_non_list_breakdown_normalised_to_empty(self):
        sensor = _make_sensor({"breakdown": "not a list"})
        attrs = sensor.extra_state_attributes
        assert "breakdown" not in attrs

    def test_ea21_attrs_non_dict_top_consumer_items_skipped(self):
        sensor = _make_sensor({"top_consumers": [None, "string", {"name": "OK"}]})
        attrs = sensor.extra_state_attributes
        assert attrs["top_consumers"] == [{"name": "OK", "monthly_kwh": 0.0}]

    def test_ea22_attrs_non_list_top_consumers_normalised_to_empty(self):
        sensor = _make_sensor({"top_consumers": 123})
        attrs = sensor.extra_state_attributes
        assert "top_consumers" not in attrs

    def test_ea23_attrs_non_dict_rec_items_skipped(self):
        sensor = _make_sensor({"recommendations": [42, "string", None, {"title_de": "Valid"}]})
        attrs = sensor.extra_state_attributes
        assert attrs["recommendations"] == [
            {"title": "Valid", "savings_eur": 0.0, "difficulty": "", "applied": None}
        ]

    def test_ea24_attrs_non_list_recs_normalised_to_empty(self):
        sensor = _make_sensor({"recommendations": {"title_de": "should be list"}})
        attrs = sensor.extra_state_attributes
        assert "recommendations" not in attrs


# ---------------------------------------------------------------------------
# Update contract
# ---------------------------------------------------------------------------

class TestEnergyAdvisorUpdateContract:
    def test_ea9_async_update_stores_only_ok_payloads(self):
        sensor = _make_sensor()

        async def fake_fetch():
            return {"ok": True, "eco_score": {"grade": "A", "score": 90}}

        sensor._fetch = fake_fetch  # type: ignore[method-assign]
        asyncio.run(sensor.async_update())
        assert sensor._data == {"ok": True, "eco_score": {"grade": "A", "score": 90}}

    def test_ea10_async_update_ignores_non_ok_payloads(self):
        sensor = _make_sensor({"ok": True, "eco_score": {"grade": "B", "score": 77}})

        async def fake_fetch():
            return {"ok": False, "eco_score": {"grade": "A", "score": 99}}

        sensor._fetch = fake_fetch  # type: ignore[method-assign]
        asyncio.run(sensor.async_update())
        assert sensor._data == {"ok": True, "eco_score": {"grade": "B", "score": 77}}

    # HA-329: non-dict response keeps previous data (silent ignore), consistent with test_ea10
    def test_ea25_async_update_keeps_data_on_non_dict_response(self):
        sensor = _make_sensor({"ok": True, "eco_score": {"grade": "A", "score": 90}})

        async def fake_fetch():
            return "not a dict"

        sensor._fetch = fake_fetch  # type: ignore[method-assign]
        asyncio.run(sensor.async_update())
        # non-dict response is silently ignored, previous data kept
        assert sensor._data == {"ok": True, "eco_score": {"grade": "A", "score": 90}}

    def test_ea26_async_update_keeps_data_on_none_response(self):
        sensor = _make_sensor({"ok": True, "eco_score": {"grade": "A", "score": 90}})

        async def fake_fetch():
            return None

        sensor._fetch = fake_fetch  # type: ignore[method-assign]
        asyncio.run(sensor.async_update())
        # None response is silently ignored, previous data kept
        assert sensor._data == {"ok": True, "eco_score": {"grade": "A", "score": 90}}


# ---------------------------------------------------------------------------
# Global contract
# ---------------------------------------------------------------------------

class TestEnergyAdvisorGlobalContract:
    def test_gc1_sensor_targets_hub_energy_endpoint_and_caps_lists(self):
        src = open("custom_components/pilotsuite/sensors/energy_advisor_sensor.py", encoding="utf-8").read()
        assert "/api/v1/hub/energy" in src
        assert "async_get_clientsession" in src
        assert "top[:5]" in src
        assert "recs[:5]" in src
        assert '"name_de"' in src
        assert '"title_de"' in src

    def test_gc2_sensor_uses_only_trivial_grade_mapping_and_projection(self):
        src = open("custom_components/pilotsuite/sensors/energy_advisor_sensor.py", encoding="utf-8").read()
        assert "_GRADE_ICONS" in src
        assert 'return f"Eco-Score {grade} ({score}/100)"' in src
        assert 'return "Nicht verfügbar"' in src
        assert "predict" not in src.lower()
        assert "neural" not in src.lower()

    # HA-329 source guards
    def test_gc3_source_guard_uses_all_type_helpers(self):
        src = open("custom_components/pilotsuite/sensors/energy_advisor_sensor.py", encoding="utf-8").read()
        assert "_as_mapping" in src
        assert "_as_list" in src
        assert "_as_float" in src
        assert "_as_int" in src
        assert "_as_string" in src
        assert "math.isfinite" in src
