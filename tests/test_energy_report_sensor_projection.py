"""Projection contract tests for EnergyReportSensor (HA-140).

Verifies:
- EnergyReportSensor: pure projection on GET /api/v1/energy/reports/usage-patterns/export

Contract verified:
- native_value: estimated_cost_impact_eur from export data, no local classification
- extra_state_attributes: direct lookups from usage-pattern export response
- edge: missing optional keys handled gracefully
- GC1: no local semantic invention
- GC2: hits correct Core endpoint
"""

from pathlib import Path

import pytest


class EnergyReportSensorContract:
    """Pure projection contract for EnergyReportSensor."""

    @staticmethod
    def native_value(report_data: dict | None) -> float | None:
        if not report_data:
            return None
        impact = report_data.get("impact") or {}
        value = impact.get("estimated_cost_impact_eur")
        return value if isinstance(value, (int, float)) else None

    @staticmethod
    def extra_state_attributes(report_data: dict | None) -> dict:
        if not report_data:
            return {
                "report_type": "usage_patterns_export",
                "period_start": "",
                "period_end": "",
                "pattern_count": 0,
                "recommendations_count": 0,
                "estimated_energy_impact_kwh": 0,
                "estimated_cost_impact_eur": 0,
                "new_patterns": 0,
                "fading_patterns": 0,
                "rising_patterns": 0,
                "top_pattern_ids": [],
            }

        window = report_data.get("window") or {}
        impact = report_data.get("impact") or {}
        drift_summary = ((report_data.get("drift") or {}).get("summary") or {})
        patterns = report_data.get("patterns") if isinstance(report_data.get("patterns"), list) else []
        recommendations = report_data.get("recommendations") if isinstance(report_data.get("recommendations"), list) else []

        return {
            "report_type": "usage_patterns_export",
            "period_start": window.get("from", ""),
            "period_end": window.get("to", ""),
            "pattern_count": len(patterns),
            "recommendations_count": len(recommendations),
            "estimated_energy_impact_kwh": impact.get("estimated_energy_impact_kwh", 0),
            "estimated_cost_impact_eur": impact.get("estimated_cost_impact_eur", 0),
            "new_patterns": drift_summary.get("new_patterns", 0),
            "fading_patterns": drift_summary.get("fading_patterns", 0),
            "rising_patterns": drift_summary.get("rising_patterns", 0),
            "top_pattern_ids": [
                pattern.get("pattern_id")
                for pattern in patterns[:3]
                if isinstance(pattern, dict) and pattern.get("pattern_id")
            ],
        }


@pytest.mark.parametrize("report_data,expected", [
    ({"impact": {"estimated_cost_impact_eur": 12.5}, "patterns": [{"pattern_id": "p1"}]}, 12.5),
    ({"impact": {"estimated_cost_impact_eur": 0.0}}, 0.0),
    ({"impact": {"estimated_cost_impact_eur": 85.3}}, 85.3),
    (None, None),
    ({}, None),
    ({"patterns": []}, None),
])
def test_er1_native_value(report_data, expected):
    assert EnergyReportSensorContract.native_value(report_data) == expected


def test_er2_attrs_full():
    report_data = {
        "window": {
            "from": "2026-03-30T00:00:00",
            "to": "2026-04-05T23:59:59",
        },
        "patterns": [
            {"pattern_id": "energy-evening-1"},
            {"pattern_id": "energy-morning-2"},
        ],
        "impact": {
            "estimated_cost_impact_eur": 18.4,
            "estimated_energy_impact_kwh": 62.3,
        },
        "drift": {"summary": {"new_patterns": 1, "fading_patterns": 0, "rising_patterns": 2}},
        "recommendations": [
            {"id": "r1", "text": "Shift laundry"},
            {"id": "r2", "text": "Pre-heat"},
        ],
    }
    attrs = EnergyReportSensorContract.extra_state_attributes(report_data)
    assert attrs == {
        "report_type": "usage_patterns_export",
        "period_start": "2026-03-30T00:00:00",
        "period_end": "2026-04-05T23:59:59",
        "pattern_count": 2,
        "recommendations_count": 2,
        "estimated_energy_impact_kwh": 62.3,
        "estimated_cost_impact_eur": 18.4,
        "new_patterns": 1,
        "fading_patterns": 0,
        "rising_patterns": 2,
        "top_pattern_ids": ["energy-evening-1", "energy-morning-2"],
    }


@pytest.mark.parametrize("report_data,expected", [
    ({}, {
        "report_type": "usage_patterns_export",
        "period_start": "",
        "period_end": "",
        "pattern_count": 0,
        "recommendations_count": 0,
        "estimated_energy_impact_kwh": 0,
        "estimated_cost_impact_eur": 0,
        "new_patterns": 0,
        "fading_patterns": 0,
        "rising_patterns": 0,
        "top_pattern_ids": [],
    }),
    (None, {
        "report_type": "usage_patterns_export",
        "period_start": "",
        "period_end": "",
        "pattern_count": 0,
        "recommendations_count": 0,
        "estimated_energy_impact_kwh": 0,
        "estimated_cost_impact_eur": 0,
        "new_patterns": 0,
        "fading_patterns": 0,
        "rising_patterns": 0,
        "top_pattern_ids": [],
    }),
    ({"impact": {"estimated_cost_impact_eur": 5.0}}, {
        "report_type": "usage_patterns_export",
        "period_start": "",
        "period_end": "",
        "pattern_count": 0,
        "recommendations_count": 0,
        "estimated_energy_impact_kwh": 0,
        "estimated_cost_impact_eur": 5.0,
        "new_patterns": 0,
        "fading_patterns": 0,
        "rising_patterns": 0,
        "top_pattern_ids": [],
    }),
    ({"window": {"from": "2026-04-01"}, "patterns": [{"pattern_id": "p1"}]}, {
        "report_type": "usage_patterns_export",
        "period_start": "2026-04-01",
        "period_end": "",
        "pattern_count": 1,
        "recommendations_count": 0,
        "estimated_energy_impact_kwh": 0,
        "estimated_cost_impact_eur": 0,
        "new_patterns": 0,
        "fading_patterns": 0,
        "rising_patterns": 0,
        "top_pattern_ids": ["p1"],
    }),
])
def test_er3_attrs_defaults(report_data, expected):
    assert EnergyReportSensorContract.extra_state_attributes(report_data) == expected


def test_gc1_no_local_semantic_invention():
    high_cost_data = {
        "impact": {"estimated_cost_impact_eur": 999.99},
        "patterns": [{"pattern_id": "p1"}],
        "recommendations": [],
    }
    assert EnergyReportSensorContract.native_value(high_cost_data) == 999.99

    low_cost_data = {
        "impact": {"estimated_cost_impact_eur": 0.01},
        "recommendations": [],
    }
    assert EnergyReportSensorContract.native_value(low_cost_data) == 0.01


def test_gc2_hits_correct_core_endpoint():
    source = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "pilotsuite"
        / "sensors"
        / "energy_report_sensor.py"
    ).read_text(encoding="utf-8")

    assert '/api/v1/energy/reports/usage-patterns/export' in source
    assert 'session.get(url, headers=headers, timeout=15)' in source
    assert 'session.post(' not in source
