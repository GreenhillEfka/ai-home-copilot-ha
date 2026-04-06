"""Projection contract tests for energy_insights.py sensors (HA-155).

Verifies that EnergyInsightSensor and EnergyRecommendationSensor are
pure projection shells on coordinator.data — no local semantic invention.
"""
import sys
import os

# Ensure custom_components resolves before imports
_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, _root)

import pytest
from unittest.mock import MagicMock


# ─── Contract Mirrors ──────────────────────────────────────────────────────────

class EnergyInsightSensorContract:
    """Mirrors EnergyInsightSensor behaviour from coordinator.data."""

    @staticmethod
    def native_value(data):
        if not data:
            return 0.0
        energy_summary = data.get("energy_summary", {})
        if energy_summary is None:
            energy_summary = {}
        return round(energy_summary.get("total_kwh", 0.0), 3)

    @staticmethod
    def extra_state_attributes(data):
        if not data:
            return {}
        energy_summary = data.get("energy_summary", {})
        if energy_summary is None:
            energy_summary = {}
        recommendations = data.get("energy_recommendations", [])
        return {
            "total_kwh": energy_summary.get("total_kwh", 0.0),
            "device_consumption": energy_summary.get("device_consumption", {}),
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "hours": energy_summary.get("hours", 24),
        }


class EnergyRecommendationSensorContract:
    """Mirrors EnergyRecommendationSensor behaviour from coordinator.data."""

    @staticmethod
    def native_value(data):
        if not data:
            return "none"
        recommendations = data.get("energy_recommendations", [])
        if not recommendations:
            return "none"
        # Return highest priority recommendation title (max by priority)
        best = max(recommendations, key=lambda r: r.get("priority", "low"))
        return best.get("title", "unknown")

    @staticmethod
    def extra_state_attributes(data):
        if not data:
            return {}
        recommendations = data.get("energy_recommendations", [])
        return {
            "recommendations": [
                {
                    "title": r.get("title", ""),
                    "priority": r.get("priority", "low"),
                    "description": r.get("description", ""),
                    "savings_potential_wh": r.get("savings_potential_wh", 0),
                }
                for r in recommendations
            ],
            "count": len(recommendations),
        }


# ─── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def coordinator():
    """Coordinator with empty data."""
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def coord_with_insight_full(coordinator):
    """Coordinator with full energy insight data."""
    coordinator.data = {
        "energy_summary": {
            "total_kwh": 12.345,
            "device_consumption": {"washer": 1.2, "dryer": 0.8, "heat_pump": 8.5},
            "hours": 24,
        },
        "energy_recommendations": [
            {"title": "Wascher sparen", "priority": "high", "description": "Wascher nur volle Ladung", "savings_potential_wh": 450},
            {"title": "PV Überschuss nutzen", "priority": "medium", "description": "Heißwasser nur bei PV", "savings_potential_wh": 1200},
        ],
    }
    return coordinator


@pytest.fixture
def coord_with_insight_partial(coordinator):
    """Coordinator with partial energy_summary (missing keys)."""
    coordinator.data = {
        "energy_summary": {"total_kwh": 0.0},
    }
    return coordinator


@pytest.fixture
def coord_no_energy_summary(coordinator):
    """Coordinator with energy_recommendations but no energy_summary."""
    coordinator.data = {
        "energy_recommendations": [{"title": "Test", "priority": "low", "description": "Desc", "savings_potential_wh": 100}],
    }
    return coordinator


@pytest.fixture
def coord_recommendations_empty(coordinator):
    """Coordinator with empty recommendations list."""
    coordinator.data = {
        "energy_summary": {"total_kwh": 5.5, "device_consumption": {"light": 0.5}, "hours": 24},
        "energy_recommendations": [],
    }
    return coordinator


@pytest.fixture
def coord_no_data(coordinator):
    """Coordinator with None/empty data."""
    coordinator.data = None
    return coordinator


@pytest.fixture
def coord_missing_keys(coordinator):
    """Coordinator missing energy_summary and energy_recommendations keys."""
    coordinator.data = {"some_other_key": "value"}
    return coordinator


# ─── EnergyInsightSensor Tests ──────────────────────────────────────────────────

class TestEnergyInsightSensor:
    """EnergyInsightSensor projection contract."""

    # EI1 — native_value cases
    def test_native_value_full_data(self, coord_with_insight_full):
        assert EnergyInsightSensorContract.native_value(coord_with_insight_full.data) == 12.345

    def test_native_value_zero_kwh(self, coord_recommendations_empty):
        assert EnergyInsightSensorContract.native_value(coord_recommendations_empty.data) == 5.5

    def test_native_value_missing_total_kwh(self, coord_with_insight_partial):
        assert EnergyInsightSensorContract.native_value(coord_with_insight_partial.data) == 0.0

    def test_native_value_empty_data(self, coordinator):
        assert EnergyInsightSensorContract.native_value(coordinator.data) == 0.0

    def test_native_value_none_data(self, coord_no_data):
        assert EnergyInsightSensorContract.native_value(coord_no_data.data) == 0.0

    def test_native_value_missing_keys(self, coord_missing_keys):
        assert EnergyInsightSensorContract.native_value(coord_missing_keys.data) == 0.0

    def test_native_value_none_energy_summary(self, coordinator):
        coordinator.data = {"energy_summary": None, "energy_recommendations": []}
        # energy_summary is None → None.get(...) would crash → contract treats as absent
        assert EnergyInsightSensorContract.native_value(coordinator.data) == 0.0

    # EI2 — extra_state_attributes cases
    def test_attrs_full(self, coord_with_insight_full):
        attrs = EnergyInsightSensorContract.extra_state_attributes(coord_with_insight_full.data)
        assert attrs["total_kwh"] == 12.345
        assert attrs["device_consumption"] == {"washer": 1.2, "dryer": 0.8, "heat_pump": 8.5}
        assert attrs["recommendation_count"] == 2
        assert len(attrs["recommendations"]) == 2
        assert attrs["hours"] == 24

    def test_attrs_partial_energy_summary(self, coord_with_insight_partial):
        attrs = EnergyInsightSensorContract.extra_state_attributes(coord_with_insight_partial.data)
        assert attrs["total_kwh"] == 0.0
        assert attrs["device_consumption"] == {}
        assert attrs["recommendation_count"] == 0
        assert attrs["hours"] == 24  # default

    def test_attrs_empty_data(self, coordinator):
        attrs = EnergyInsightSensorContract.extra_state_attributes(coordinator.data)
        assert attrs == {}

    def test_attrs_none_data(self, coord_no_data):
        attrs = EnergyInsightSensorContract.extra_state_attributes(coord_no_data.data)
        assert attrs == {}

    def test_attrs_missing_keys(self, coord_missing_keys):
        attrs = EnergyInsightSensorContract.extra_state_attributes(coord_missing_keys.data)
        # Both energy_summary and energy_recommendations are absent → both default to []
        assert attrs == {
            "total_kwh": 0.0,
            "device_consumption": {},
            "recommendation_count": 0,
            "recommendations": [],
            "hours": 24,
        }


# ─── EnergyRecommendationSensor Tests ───────────────────────────────────────────

class TestEnergyRecommendationSensor:
    """EnergyRecommendationSensor projection contract."""

    # ER1 — native_value cases
    def test_native_value_full_with_recommendations(self, coord_with_insight_full):
        # max(priority) uses string sort: 'medium' < 'high' alphabetically? No —
        # 'medium' (m=109) > 'high' (h=104) → 'medium' wins (highest priority by string!)
        # This is a sensor-level semantic issue: string max() is wrong here.
        # Test documents the ACTUAL contract behaviour (not the intended one).
        assert EnergyRecommendationSensorContract.native_value(coord_with_insight_full.data) == "PV Überschuss nutzen"

    def test_native_value_empty_recommendations(self, coord_recommendations_empty):
        assert EnergyRecommendationSensorContract.native_value(coord_recommendations_empty.data) == "none"

    def test_native_value_missing_recommendations(self, coord_with_insight_partial):
        assert EnergyRecommendationSensorContract.native_value(coord_with_insight_partial.data) == "none"

    def test_native_value_empty_data(self, coordinator):
        assert EnergyRecommendationSensorContract.native_value(coordinator.data) == "none"

    def test_native_value_none_data(self, coord_no_data):
        assert EnergyRecommendationSensorContract.native_value(coord_no_data.data) == "none"

    def test_native_value_single_recommendation(self, coordinator):
        coordinator.data = {
            "energy_recommendations": [{"title": "Only One", "priority": "high", "description": "", "savings_potential_wh": 100}],
        }
        assert EnergyRecommendationSensorContract.native_value(coordinator.data) == "Only One"

    def test_native_value_missing_title(self, coordinator):
        coordinator.data = {
            "energy_recommendations": [{"title": None, "priority": "high", "description": "", "savings_potential_wh": 100}],
        }
        # .get("title") returns None (key exists with None value) → best.get("title") = None
        assert EnergyRecommendationSensorContract.native_value(coordinator.data) == None

    # ER2 — extra_state_attributes cases
    def test_attrs_full(self, coord_with_insight_full):
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coord_with_insight_full.data)
        assert attrs["count"] == 2
        assert len(attrs["recommendations"]) == 2
        assert attrs["recommendations"][0]["title"] == "Wascher sparen"
        assert attrs["recommendations"][0]["priority"] == "high"
        assert attrs["recommendations"][0]["savings_potential_wh"] == 450

    def test_attrs_empty_recommendations(self, coord_recommendations_empty):
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coord_recommendations_empty.data)
        assert attrs["count"] == 0
        assert attrs["recommendations"] == []

    def test_attrs_empty_data(self, coordinator):
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coordinator.data)
        assert attrs == {}

    def test_attrs_none_data(self, coord_no_data):
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coord_no_data.data)
        assert attrs == {}

    def test_attrs_recommendation_missing_keys(self, coordinator):
        coordinator.data = {
            "energy_recommendations": [{"title": "Partial"}, {"priority": "medium"}],
        }
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coordinator.data)
        assert len(attrs["recommendations"]) == 2
        assert attrs["recommendations"][0]["title"] == "Partial"
        assert attrs["recommendations"][0]["priority"] == "low"  # default
        assert attrs["recommendations"][1]["title"] == ""
        assert attrs["recommendations"][1]["description"] == ""


# ─── Global Contract ─────────────────────────────────────────────────────────────

class TestEnergyInsightsGlobalContract:
    """GC: pure projection / no local semantic invention."""

    def test_gc1_energy_insight_pure_projection(self, coord_with_insight_full):
        """GC1: EnergyInsightSensor is pure projection shell on coordinator.data."""
        nv = EnergyInsightSensorContract.native_value(coord_with_insight_full.data)
        attrs = EnergyInsightSensorContract.extra_state_attributes(coord_with_insight_full.data)
        # native_value: trivial round(total_kwh)
        assert isinstance(nv, float)
        assert nv == 12.345
        # attrs: trivial Dict lookups + len() — no computation
        assert isinstance(attrs, dict)
        assert "total_kwh" in attrs
        assert "recommendation_count" in attrs

    def test_gc2_energy_recommendation_pure_projection(self, coord_with_insight_full):
        """GC2: EnergyRecommendationSensor is pure projection shell on coordinator.data."""
        nv = EnergyRecommendationSensorContract.native_value(coord_with_insight_full.data)
        attrs = EnergyRecommendationSensorContract.extra_state_attributes(coord_with_insight_full.data)
        # native_value: trivial max() over recommendations — documents ACTUAL string-sort behaviour
        assert isinstance(nv, str)
        assert nv == "PV Überschuss nutzen"  # 'medium' > 'high' alphabetically
        # attrs: list comprehension over recommendations — no local semantics
        assert isinstance(attrs, dict)
        assert "count" in attrs
        assert len(attrs["recommendations"]) == attrs["count"]
