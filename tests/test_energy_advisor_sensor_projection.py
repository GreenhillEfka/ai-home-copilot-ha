"""Projection contract tests for energy_advisor_sensor.py.

Verifies EnergyAdvisorSensor is a pure projection shell on
`/api/v1/hub/energy` data with only trivial formatting and list trimming.

HA-254
"""

from __future__ import annotations

import asyncio

import pytest

from custom_components.pilotsuite.sensors.energy_advisor_sensor import EnergyAdvisorSensor


class EnergyAdvisorSensorContract:
    """Mirror of EnergyAdvisorSensor projection logic."""

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
        eco = (data or {}).get("eco_score", {})
        grade = eco.get("grade", "?")
        score = eco.get("score", 0)
        if not eco:
            return "Nicht verfügbar"
        return f"Eco-Score {grade} ({score}/100)"

    @staticmethod
    def icon(data: dict) -> str:
        eco = (data or {}).get("eco_score", {})
        grade = eco.get("grade", "C")
        return EnergyAdvisorSensorContract._GRADE_ICONS.get(grade, "mdi:flash")

    @staticmethod
    def attrs(data: dict) -> dict:
        eco = (data or {}).get("eco_score", {})
        attrs = {
            "eco_score": eco.get("score", 0),
            "eco_grade": eco.get("grade", "?"),
            "eco_trend": eco.get("trend", "stabil"),
            "total_daily_kwh": (data or {}).get("total_daily_kwh", 0),
            "total_monthly_kwh": (data or {}).get("total_monthly_kwh", 0),
            "total_monthly_eur": (data or {}).get("total_monthly_eur", 0),
            "savings_potential_eur": (data or {}).get("savings_potential_eur", 0),
        }

        breakdown = (data or {}).get("breakdown", [])
        if breakdown:
            attrs["breakdown"] = [
                {
                    "category": item.get("name_de"),
                    "kwh": item.get("kwh"),
                    "pct": item.get("pct"),
                }
                for item in breakdown
            ]

        top = (data or {}).get("top_consumers", [])
        if top:
            attrs["top_consumers"] = [
                {
                    "name": item.get("name"),
                    "monthly_kwh": item.get("monthly_kwh"),
                }
                for item in top[:5]
            ]

        recs = (data or {}).get("recommendations", [])
        if recs:
            attrs["recommendations"] = [
                {
                    "title": item.get("title_de"),
                    "savings_eur": item.get("potential_savings_eur"),
                    "difficulty": item.get("difficulty"),
                    "applied": item.get("applied"),
                }
                for item in recs[:5]
            ]

        return attrs


class FakeCoordinator:
    def __init__(self) -> None:
        self._config = {}
        self.data = {}


def _make_sensor(data: dict | None = None) -> EnergyAdvisorSensor:
    sensor = EnergyAdvisorSensor(FakeCoordinator())
    sensor._data = data if isinstance(data, dict) else {}
    return sensor


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


class TestEnergyAdvisorAttrs:
    def test_ea5_attrs_defaults_when_empty(self):
        sensor = _make_sensor({})
        assert sensor.extra_state_attributes == {
            "eco_score": 0,
            "eco_grade": "?",
            "eco_trend": "stabil",
            "total_daily_kwh": 0,
            "total_monthly_kwh": 0,
            "total_monthly_eur": 0,
            "savings_potential_eur": 0,
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
        assert attrs["top_consumers"][0] == {"name": "consumer-0", "monthly_kwh": 0}
        assert attrs["top_consumers"][-1] == {"name": "consumer-4", "monthly_kwh": 40}
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

    def test_ea8_attrs_keep_none_values_without_local_cleanup(self):
        sensor = _make_sensor(
            {
                "eco_score": {"grade": None, "score": None, "trend": None},
                "breakdown": [{"name_de": None, "kwh": None, "pct": None}],
                "top_consumers": [{"name": None, "monthly_kwh": None}],
                "recommendations": [
                    {
                        "title_de": None,
                        "potential_savings_eur": None,
                        "difficulty": None,
                        "applied": None,
                    }
                ],
            }
        )
        assert sensor.extra_state_attributes == {
            "eco_score": None,
            "eco_grade": None,
            "eco_trend": None,
            "total_daily_kwh": 0,
            "total_monthly_kwh": 0,
            "total_monthly_eur": 0,
            "savings_potential_eur": 0,
            "breakdown": [{"category": None, "kwh": None, "pct": None}],
            "top_consumers": [{"name": None, "monthly_kwh": None}],
            "recommendations": [
                {
                    "title": None,
                    "savings_eur": None,
                    "difficulty": None,
                    "applied": None,
                }
            ],
        }


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
