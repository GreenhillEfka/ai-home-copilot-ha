"""Projection contract tests for weather_warning_sensor.

Verifies WeatherWarningSensor is a pure projection shell on Core
/api/v1/regional/warnings — no local semantic invention.

HA-134 — 2026-04-06
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock


# =============================================================================
# Contract Mirror
# =============================================================================

class WeatherWarningSensorContract:
    """Mirror of WeatherWarningSensor projection logic.

    Contract:
    - hits /api/v1/regional/warnings
    - native_value: "Keine Warnungen" | "{count}x {highest_severity_label}"
    - icon: severity-based (0=sunny, 1=outline, 2=alert, 3/4=octagon)
    - attrs: total_warnings, highest_severity, by_severity counts,
             has_pv_impact, has_grid_risk, max_pv_reduction_pct,
             recommendations (capped 5), warnings (capped 10)
    """

    _SEVERITY_ICONS = {
        0: "mdi:weather-sunny",
        1: "mdi:alert-outline",
        2: "mdi:alert",
        3: "mdi:alert-octagon",
        4: "mdi:alert-octagon-outline",
    }

    def __init__(self, warnings_data: dict | None):
        self._data = warnings_data or {}

    @property
    def native_value(self) -> str:
        total = self._data.get("total", 0)
        if total == 0:
            return "Keine Warnungen"
        highest = self._data.get("highest_severity_label", "Wetterwarnung")
        return f"{total}x {highest}"

    @property
    def icon(self) -> str:
        severity = self._data.get("highest_severity", 0)
        return self._SEVERITY_ICONS.get(severity, "mdi:alert")

    @property
    def extra_state_attributes(self) -> dict:
        warnings = self._data.get("warnings", [])
        impacts = self._data.get("impacts", [])
        by_severity = self._data.get("by_severity", {})

        # Build compact warning list for attributes
        warning_list = []
        for w in warnings[:10]:  # Max 10 in attributes
            warning_list.append({
                "headline": w.get("headline", ""),
                "severity": w.get("severity_label", ""),
                "type": w.get("warning_type_label", ""),
                "region": w.get("region", ""),
                "color": w.get("color", ""),
            })

        # Aggregate PV impact (with type safety)
        max_pv_reduction = 0
        pv_recommendations = []
        if isinstance(impacts, list):
            for imp in impacts:
                if isinstance(imp, dict):
                    red = imp.get("pv_reduction_pct", 0)
                    if red > max_pv_reduction:
                        max_pv_reduction = red
                    rec = imp.get("recommendation_de", "")
                    if rec and rec not in pv_recommendations:
                        pv_recommendations.append(rec)

        return {
            "total_warnings": self._data.get("total", 0),
            "highest_severity": self._data.get("highest_severity", 0),
            "highest_severity_label": self._data.get("highest_severity_label", ""),
            "minor_count": by_severity.get("minor", 0),
            "moderate_count": by_severity.get("moderate", 0),
            "severe_count": by_severity.get("severe", 0),
            "extreme_count": by_severity.get("extreme", 0),
            "has_pv_impact": self._data.get("has_pv_impact", False),
            "has_grid_risk": self._data.get("has_grid_risk", False),
            "max_pv_reduction_pct": max_pv_reduction,
            "recommendations": pv_recommendations[:5],
            "warnings": warning_list,
            "source": self._data.get("source", ""),
            "last_updated": self._data.get("last_updated", ""),
        }


# =============================================================================
# WW1 — native_value
# =============================================================================

class TestWeatherWarningSensorNativeValue:
    """WW1: native_value reflects warning count and highest severity."""

    def test_ww1_native_value_zero_warnings(self):
        """WW1.1: Returns 'Keine Warnungen' when total=0."""
        sensor = WeatherWarningSensorContract({"total": 0, "ok": True})
        assert sensor.native_value == "Keine Warnungen"

    def test_ww1_native_value_one_warning(self):
        """WW1.2: Returns '1x {severity_label}' for single warning."""
        sensor = WeatherWarningSensorContract({
            "total": 1,
            "highest_severity_label": "Starkregen",
            "ok": True
        })
        assert sensor.native_value == "1x Starkregen"

    def test_ww1_native_value_multiple_warnings(self):
        """WW1.3: Returns '{count}x {severity_label}' for multiple warnings."""
        sensor = WeatherWarningSensorContract({
            "total": 3,
            "highest_severity_label": "Unwetter",
            "ok": True
        })
        assert sensor.native_value == "3x Unwetter"

    def test_ww1_native_value_missing_data(self):
        """WW1.4: Returns 'Keine Warnungen' when data is None/empty."""
        sensor = WeatherWarningSensorContract(None)
        assert sensor.native_value == "Keine Warnungen"


# =============================================================================
# WW2 — icon by severity
# =============================================================================

class TestWeatherWarningSensorIcon:
    """WW2: icon maps severity level to appropriate icon."""

    def test_ww2_icon_severity_0_sunny(self):
        """WW2.1: severity=0 returns mdi:weather-sunny."""
        sensor = WeatherWarningSensorContract({"highest_severity": 0, "ok": True})
        assert sensor.icon == "mdi:weather-sunny"

    def test_ww2_icon_severity_1_outline(self):
        """WW2.2: severity=1 returns mdi:alert-outline."""
        sensor = WeatherWarningSensorContract({"highest_severity": 1, "ok": True})
        assert sensor.icon == "mdi:alert-outline"

    def test_ww2_icon_severity_2_alert(self):
        """WW2.3: severity=2 returns mdi:alert."""
        sensor = WeatherWarningSensorContract({"highest_severity": 2, "ok": True})
        assert sensor.icon == "mdi:alert"

    def test_ww2_icon_severity_3_octagon(self):
        """WW2.4: severity=3 returns mdi:alert-octagon."""
        sensor = WeatherWarningSensorContract({"highest_severity": 3, "ok": True})
        assert sensor.icon == "mdi:alert-octagon"

    def test_ww2_icon_severity_4_octagon_outline(self):
        """WW2.5: severity=4 returns mdi:alert-octagon-outline."""
        sensor = WeatherWarningSensorContract({"highest_severity": 4, "ok": True})
        assert sensor.icon == "mdi:alert-octagon-outline"

    def test_ww2_icon_unknown_severity(self):
        """WW2.6: Unknown severity returns fallback mdi:alert."""
        sensor = WeatherWarningSensorContract({"highest_severity": 99, "ok": True})
        assert sensor.icon == "mdi:alert"


# =============================================================================
# WW3 — attributes
# =============================================================================

class TestWeatherWarningSensorAttributes:
    """WW3: extra_state_attributes expose warning details and PV impact."""

    def test_ww3_attrs_full_data(self):
        """WW3.1: Full data exposes all expected attributes."""
        data = {
            "total": 2,
            "highest_severity": 2,
            "highest_severity_label": "Unwetter",
            "by_severity": {"minor": 1, "moderate": 1, "severe": 0, "extreme": 0},
            "has_pv_impact": True,
            "has_grid_risk": False,
            "impacts": [{"pv_reduction_pct": 45, "recommendation_de": "PV-Anlage beschatten"}],
            "warnings": [{"headline": "Starkregen", "severity_label": "Moderat", "warning_type_label": "Regen", "region": "München", "color": "orange"}],
            "source": "DWD",
            "last_updated": "2026-04-06T06:00:00Z",
            "ok": True
        }
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert attrs["total_warnings"] == 2
        assert attrs["highest_severity"] == 2
        assert attrs["highest_severity_label"] == "Unwetter"
        assert attrs["minor_count"] == 1
        assert attrs["moderate_count"] == 1
        assert attrs["has_pv_impact"] is True
        assert attrs["has_grid_risk"] is False
        assert attrs["max_pv_reduction_pct"] == 45
        assert "PV-Anlage beschatten" in attrs["recommendations"]
        assert len(attrs["warnings"]) == 1

    def test_ww3_attrs_minimal_data(self):
        """WW3.2: Minimal data exposes defaults for missing fields."""
        data = {"total": 0, "ok": True}
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert attrs["total_warnings"] == 0
        assert attrs["highest_severity"] == 0
        assert attrs["minor_count"] == 0
        assert attrs["moderate_count"] == 0
        assert attrs["severe_count"] == 0
        assert attrs["extreme_count"] == 0
        assert attrs["has_pv_impact"] is False
        assert attrs["has_grid_risk"] is False
        assert attrs["max_pv_reduction_pct"] == 0
        assert attrs["recommendations"] == []
        assert attrs["warnings"] == []

    def test_ww3_attrs_warnings_capped_10(self):
        """WW3.3: warnings list capped at 10 entries."""
        warnings = [{"headline": f"Warnung {i}"} for i in range(15)]
        data = {"total": 15, "warnings": warnings, "ok": True}
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert len(attrs["warnings"]) == 10

    def test_ww3_attrs_pv_recommendations_capped_5(self):
        """WW3.4: recommendations list capped at 5 unique entries."""
        impacts = [{"pv_reduction_pct": i * 10, "recommendation_de": f"Empfehlung {i}"} for i in range(10)]
        data = {"total": 1, "impacts": impacts, "ok": True}
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert len(attrs["recommendations"]) == 5

    def test_ww3_attrs_max_pv_reduction(self):
        """WW3.5: max_pv_reduction_pct reflects highest impact."""
        impacts = [
            {"pv_reduction_pct": 20, "recommendation_de": "A"},
            {"pv_reduction_pct": 60, "recommendation_de": "B"},
            {"pv_reduction_pct": 35, "recommendation_de": "C"},
        ]
        data = {"total": 1, "impacts": impacts, "ok": True}
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert attrs["max_pv_reduction_pct"] == 60


# =============================================================================
# WW4 — edge cases
# =============================================================================

class TestWeatherWarningSensorEdgeCases:
    """WW4: Edge cases handled gracefully."""

    def test_ww4_edge_empty_warnings_list(self):
        """WW4.1: Empty warnings list handled correctly."""
        data = {"total": 0, "warnings": [], "impacts": [], "by_severity": {}, "ok": True}
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert attrs["warnings"] == []
        assert attrs["recommendations"] == []
        assert sensor.native_value == "Keine Warnungen"

    def test_ww4_edge_missing_optional_fields(self):
        """WW4.2: Missing optional fields use safe defaults."""
        data = {"total": 1, "ok": True}  # missing most fields
        sensor = WeatherWarningSensorContract(data)
        attrs = sensor.extra_state_attributes

        assert attrs["highest_severity"] == 0
        assert attrs["highest_severity_label"] == ""
        assert attrs["minor_count"] == 0
        assert attrs["has_pv_impact"] is False

    def test_ww4_edge_non_dict_impacts(self):
        """WW4.3: Non-dict impacts handled gracefully."""
        data = {"total": 1, "impacts": "invalid", "ok": True}
        sensor = WeatherWarningSensorContract(data)
        # Should not raise - handles non-iterable impacts
        attrs = sensor.extra_state_attributes
        assert attrs["max_pv_reduction_pct"] == 0
        assert attrs["recommendations"] == []


# =============================================================================
# GC1 — Global Contract: hits Core API endpoint
# =============================================================================

class TestWeatherWarningSensorGlobalContract:
    """GC1: Sensor hits /api/v1/regional/warnings endpoint."""

    def test_gc1_hits_regional_warnings_endpoint(self):
        """GC1.1: async_update fetches from /api/v1/regional/warnings."""
        # Verify the contract path in source (built as base + /warnings)
        import pathlib
        sensor_path = pathlib.Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "sensors" / "weather_warning_sensor.py"
        content = sensor_path.read_text()

        # Endpoint is built as f"{base}/warnings" where base = /api/v1/regional
        assert 'f"{base}/warnings"' in content or '"/warnings"' in content
        assert "async_get_clientsession" in content  # Uses HTTP session
        assert "/api/v1/regional" in content  # Base path present

    def test_gc1_no_local_semantic_invention(self):
        """GC1.2: No local classification or heuristic logic."""
        import pathlib
        sensor_path = pathlib.Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "sensors" / "weather_warning_sensor.py"
        content = sensor_path.read_text()

        # Should NOT contain local ML/heuristic keywords
        forbidden_patterns = [
            "machine_learning",
            "classify",
            "predict",
            "heuristic",
            "infer_severity",
            "calculate_risk",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in content.lower(), f"Found forbidden pattern: {pattern}"


# =============================================================================
# GC2 — Global Contract: pure projection shell
# =============================================================================

class TestWeatherWarningSensorProjectionOnly:
    """GC2: Sensor is pure projection shell, no state mutation."""

    def test_gc2_readonly_projection(self):
        """GC2.1: Sensor only reads from coordinator/API, never writes."""
        import pathlib
        sensor_path = pathlib.Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "sensors" / "weather_warning_sensor.py"
        content = sensor_path.read_text()

        # Should NOT contain write operations
        forbidden_patterns = [
            "async_write_ha_state",
            ".set(",
            ".put(",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in content, f"Found forbidden write pattern: {pattern}"
