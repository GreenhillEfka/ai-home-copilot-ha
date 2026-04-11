"""Projection contract tests for energy_insights.py sensors.

Covers malformed payload hardening for EnergyInsightSensor and
EnergyRecommendationSensor while keeping them pure projection shells on
coordinator.data.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest


class EnergyInsightSensorContract:
    """Mirror of EnergyInsightSensor behaviour."""

    @staticmethod
    def _as_mapping(value):
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _as_list(value):
        return value if isinstance(value, list) else []

    @staticmethod
    def _as_number(value, default):
        if isinstance(value, bool):
            return default
        if not isinstance(value, (int, float)):
            return default
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            return default
        return value if isinstance(value, int) else numeric_value

    @staticmethod
    def _as_string(value, default: str) -> str:
        return value if isinstance(value, str) and value else default

    @staticmethod
    def _project_recommendation(value):
        recommendation = EnergyInsightSensorContract._as_mapping(value)
        if not recommendation:
            return {}
        return {
            "title": EnergyInsightSensorContract._as_string(recommendation.get("title"), ""),
            "priority": EnergyInsightSensorContract._as_string(recommendation.get("priority"), "low"),
            "description": EnergyInsightSensorContract._as_string(recommendation.get("description"), ""),
            "savings_potential_wh": EnergyInsightSensorContract._as_number(
                recommendation.get("savings_potential_wh"),
                0,
            ),
        }

    @staticmethod
    def native_value(data):
        coordinator_data = EnergyInsightSensorContract._as_mapping(data)
        if not coordinator_data:
            return 0.0
        energy_summary = EnergyInsightSensorContract._as_mapping(
            coordinator_data.get("energy_summary")
        )
        total_kwh = EnergyInsightSensorContract._as_number(
            energy_summary.get("total_kwh"),
            0.0,
        )
        return round(float(total_kwh), 3)

    @staticmethod
    def extra_state_attributes(data):
        coordinator_data = EnergyInsightSensorContract._as_mapping(data)
        if not coordinator_data:
            return {}
        energy_summary = EnergyInsightSensorContract._as_mapping(
            coordinator_data.get("energy_summary")
        )
        recommendations = [
            projected
            for item in EnergyInsightSensorContract._as_list(
                coordinator_data.get("energy_recommendations")
            )
            if (projected := EnergyInsightSensorContract._project_recommendation(item))
        ]
        return {
            "total_kwh": EnergyInsightSensorContract._as_number(
                energy_summary.get("total_kwh"),
                0.0,
            ),
            "device_consumption": EnergyInsightSensorContract._as_mapping(
                energy_summary.get("device_consumption")
            ),
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "hours": EnergyInsightSensorContract._as_number(energy_summary.get("hours"), 24),
        }


class EnergyRecommendationSensorContract:
    """Mirror of EnergyRecommendationSensor behaviour."""

    @staticmethod
    def native_value(data):
        coordinator_data = EnergyInsightSensorContract._as_mapping(data)
        if not coordinator_data:
            return "none"
        recommendations = [
            projected
            for item in EnergyInsightSensorContract._as_list(
                coordinator_data.get("energy_recommendations")
            )
            if (projected := EnergyInsightSensorContract._project_recommendation(item))
        ]
        if not recommendations:
            return "none"
        best = max(recommendations, key=lambda recommendation: recommendation.get("priority", "low"))
        return EnergyInsightSensorContract._as_string(best.get("title"), "unknown")

    @staticmethod
    def extra_state_attributes(data):
        coordinator_data = EnergyInsightSensorContract._as_mapping(data)
        if not coordinator_data:
            return {}
        recommendations = [
            projected
            for item in EnergyInsightSensorContract._as_list(
                coordinator_data.get("energy_recommendations")
            )
            if (projected := EnergyInsightSensorContract._project_recommendation(item))
        ]
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
        }


@pytest.mark.parametrize(
    "coordinator_data, expected",
    [
        (
            {
                "energy_summary": {
                    "total_kwh": 12.3456,
                    "device_consumption": {"washer": 1.2},
                    "hours": 24,
                }
            },
            12.346,
        ),
        ({"energy_summary": {"total_kwh": 0}}, 0.0),
        ({"energy_summary": {"total_kwh": "12.3"}}, 0.0),
        ({"energy_summary": {"total_kwh": True}}, 0.0),
        ({"energy_summary": {"total_kwh": float("inf")}}, 0.0),
        ({"energy_summary": ["bad-payload"]}, 0.0),
        (["bad-top-level"], 0.0),
        ({}, 0.0),
    ],
)
def test_ei1_native_value(coordinator_data, expected):
    assert EnergyInsightSensorContract.native_value(coordinator_data) == expected


@pytest.mark.parametrize(
    "coordinator_data, key, expected",
    [
        (
            {
                "energy_summary": {
                    "total_kwh": 12.345,
                    "device_consumption": {"washer": 1.2, "dryer": 0.8},
                    "hours": 24,
                },
                "energy_recommendations": [
                    {
                        "title": "Wascher sparen",
                        "priority": "high",
                        "description": "Nur volle Ladung",
                        "savings_potential_wh": 450,
                    },
                    {
                        "title": "PV Überschuss nutzen",
                        "priority": "medium",
                        "description": "Heißwasser tagsüber",
                        "savings_potential_wh": 1200,
                    },
                ],
            },
            None,
            {
                "total_kwh": 12.345,
                "device_consumption": {"washer": 1.2, "dryer": 0.8},
                "recommendations": [
                    {
                        "title": "Wascher sparen",
                        "priority": "high",
                        "description": "Nur volle Ladung",
                        "savings_potential_wh": 450,
                    },
                    {
                        "title": "PV Überschuss nutzen",
                        "priority": "medium",
                        "description": "Heißwasser tagsüber",
                        "savings_potential_wh": 1200,
                    },
                ],
                "recommendation_count": 2,
                "hours": 24,
            },
        ),
        ({"energy_summary": {"device_consumption": []}}, "device_consumption", {}),
        ({"energy_summary": {"hours": "24"}}, "hours", 24),
        ({"energy_summary": {"hours": True}}, "hours", 24),
        ({"energy_summary": {"total_kwh": {"bad": 1}}}, "total_kwh", 0.0),
        ({"energy_recommendations": "save-now"}, "recommendations", []),
        (
            {
                "energy_recommendations": [
                    {"title": "A", "priority": "high", "description": "x", "savings_potential_wh": 100},
                    "bad",
                    {"title": None, "priority": 5, "description": ["x"], "savings_potential_wh": float("nan")},
                ]
            },
            "recommendations",
            [
                {"title": "A", "priority": "high", "description": "x", "savings_potential_wh": 100},
                {"title": "", "priority": "low", "description": "", "savings_potential_wh": 0},
            ],
        ),
        (["bad-top-level"], None, {}),
    ],
)
def test_ei2_extra_state_attributes(coordinator_data, key, expected):
    attrs = EnergyInsightSensorContract.extra_state_attributes(coordinator_data)
    if key is None:
        assert attrs == expected
        return
    assert attrs[key] == expected


@pytest.mark.parametrize(
    "coordinator_data, expected",
    [
        ({}, "none"),
        (["bad-top-level"], "none"),
        ({"energy_recommendations": []}, "none"),
        ({"energy_recommendations": "bad"}, "none"),
        (
            {
                "energy_recommendations": [
                    {"title": "Wascher sparen", "priority": "high"},
                    {"title": "PV Überschuss nutzen", "priority": "medium"},
                ]
            },
            "PV Überschuss nutzen",
        ),
        (
            {
                "energy_recommendations": [
                    "bad",
                    {"title": None, "priority": "high", "description": "x", "savings_potential_wh": 100},
                ]
            },
            "unknown",
        ),
        (
            {
                "energy_recommendations": [
                    {"title": "A", "priority": None},
                    {"title": "B", "priority": True},
                ]
            },
            "A",
        ),
    ],
)
def test_er1_native_value(coordinator_data, expected):
    assert EnergyRecommendationSensorContract.native_value(coordinator_data) == expected


@pytest.mark.parametrize(
    "coordinator_data, expected",
    [
        ({}, {}),
        (["bad-top-level"], {}),
        (
            {
                "energy_recommendations": [
                    {"title": "A", "priority": "high", "description": "x", "savings_potential_wh": 100},
                    "bad",
                    {"title": None, "priority": 3, "description": ["x"], "savings_potential_wh": float("inf")},
                ]
            },
            {
                "recommendations": [
                    {"title": "A", "priority": "high", "description": "x", "savings_potential_wh": 100},
                    {"title": "", "priority": "low", "description": "", "savings_potential_wh": 0},
                ],
                "count": 2,
            },
        ),
    ],
)
def test_er2_extra_state_attributes(coordinator_data, expected):
    assert EnergyRecommendationSensorContract.extra_state_attributes(coordinator_data) == expected


def test_gc1_recommendation_sensor_shares_the_same_projection_backbone():
    data = {
        "energy_summary": {"total_kwh": 9.25},
        "energy_recommendations": [
            {"title": "A", "priority": "high", "description": "x", "savings_potential_wh": 100}
        ],
    }
    insight_attrs = EnergyInsightSensorContract.extra_state_attributes(data)
    recommendation_attrs = EnergyRecommendationSensorContract.extra_state_attributes(data)

    assert insight_attrs["recommendation_count"] == recommendation_attrs["count"]
    assert insight_attrs["recommendations"] == recommendation_attrs["recommendations"]


def test_gc2_source_hardens_energy_insights_against_malformed_payloads():
    source = (
        Path(__file__).parent.parent
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "energy_insights.py"
    ).read_text()

    assert 'import math' in source
    assert 'def _as_mapping(value: Any) -> Dict[str, Any]:' in source
    assert 'def _as_list(value: Any) -> list[Any]:' in source
    assert 'def _as_number(value: Any, default: int | float) -> int | float:' in source
    assert 'def _as_string(value: Any, default: str) -> str:' in source
    assert 'def _project_recommendation(value: Any) -> Dict[str, Any]:' in source
    assert 'if isinstance(value, bool):' in source
    assert 'math.isfinite' in source
    assert 'coordinator_data = _as_mapping(self.coordinator.data)' in source
    assert 'energy_summary = _as_mapping(coordinator_data.get("energy_summary"))' in source
    assert 'for item in _as_list(coordinator_data.get("energy_recommendations"))' in source
    assert 'if (projected := _project_recommendation(item))' in source
    assert 'return _as_string(best.get("title"), "unknown")' in source


def test_gc3_energy_insights_unique_id_guard() -> None:
    """GC3: EnergyInsightSensor and EnergyRecommendationSensor use pilotsuite canonical unique IDs."""
    import inspect
    from custom_components.pilotsuite.sensors.energy_insights import (
        EnergyInsightSensor,
        EnergyRecommendationSensor,
    )
    
    insights_source = inspect.getsource(EnergyInsightSensor)
    recs_source = inspect.getsource(EnergyRecommendationSensor)
    
    # Must use pilotsuite canonical IDs
    assert 'pilotsuite_energy_insights' in insights_source
    assert 'pilotsuite_energy_recommendations' in recs_source
    # Must NOT contain stale ai_copilot prefixes
    assert 'ai_copilot_energy_insights' not in insights_source
    assert 'ai_copilot_energy_recommendations' not in recs_source
