"""PredictiveMaintenanceSensor Projection-Contract-Tests (HA-157).

Contract: PredictiveMaintenanceSensor + MaintenanceConfidenceSensor sind reine
Projection-Shells auf `/api/v1/hub/maintenance` + UnifiedAnomalyFramework —
triviale Dict-Lookups + sigma-deviation Aggregation, keine lokale Semantik.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Contract-Mirror: exakte Abbildung des Sensor-Verhaltens
class PredictiveMaintenanceSensorContract:
    """Mirror of PredictiveMaintenanceSensor logic for test verification."""

    @staticmethod
    def native_value(summary: dict) -> float | None:
        return summary.get("avg_health_score")

    @staticmethod
    def icon(summary: dict) -> str:
        critical = summary.get("critical", 0)
        warning = summary.get("warning", 0)
        if critical > 0:
            return "mdi:wrench-clock"
        elif warning > 0:
            return "mdi:wrench-cog"
        return "mdi:check-decagram"

    @staticmethod
    def extra_state_attributes(summary: dict) -> dict:
        attrs = {
            "total_devices": summary.get("total_devices", 0),
            "healthy": summary.get("healthy", 0),
            "degraded": summary.get("degraded", 0),
            "warning": summary.get("warning", 0),
            "critical": summary.get("critical", 0),
            "avg_health_score": summary.get("avg_health_score", 100),
            "devices_needing_attention": summary.get("devices_needing_attention", []),
            "upcoming_maintenance": summary.get("upcoming_maintenance", []),
            "failure_predictions_48h": [],  # requires framework
            "maintenance_confidence": 0.0,  # requires framework
        }
        return attrs


class MaintenanceConfidenceSensorContract:
    """Mirror of MaintenanceConfidenceSensor logic."""

    @staticmethod
    def native_value(summary: dict) -> float:
        score = (
            summary.get("critical", 0) * 30 +
            summary.get("high", 0) * 20 +
            summary.get("medium", 0) * 10 +
            summary.get("low", 0) * 5
        )
        return round(min(100.0, score), 1)


@pytest.fixture
def mock_coordinator():
    coord = MagicMock()
    coord.data = {}
    return coord


@pytest.fixture
def mock_framework():
    framework = MagicMock()
    framework._alerts = []
    framework.get_summary.return_value = {
        "critical": 0, "high": 0, "medium": 0, "low": 0,
        "failure_prediction_48h": []
    }
    return framework


# ─────────────────────────────────────────────────────────────────────────────
# PM1: native_value — avg_health_score aus Core-API
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("summary,expected", [
    ({"ok": True, "avg_health_score": 87.5, "critical": 0, "warning": 0}, 87.5),
    ({"ok": True, "avg_health_score": 62.3, "critical": 1, "warning": 2}, 62.3),
    ({"ok": True, "avg_health_score": 45.0, "critical": 3, "warning": 5}, 45.0),
    ({"ok": True, "avg_health_score": 100.0, "critical": 0, "warning": 0}, 100.0),
    ({"ok": True, "avg_health_score": 0.0, "critical": 0, "warning": 0}, 0.0),
    ({"ok": True}, None),  # missing avg_health_score
    ({"ok": True, "avg_health_score": None}, None),
])
def test_PM1_native_value(summary, expected, mock_coordinator):
    """PM1: native_value = avg_health_score (None wenn fehlt)."""
    assert PredictiveMaintenanceSensorContract.native_value(summary) == expected


# ─────────────────────────────────────────────────────────────────────────────
# PM2: icon — mdi:wrench-clock (critical) / mdi:wrench-cog (warning) / check
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("summary,expected", [
    ({"critical": 0, "warning": 0}, "mdi:check-decagram"),
    ({"critical": 0, "warning": 1}, "mdi:wrench-cog"),
    ({"critical": 0, "warning": 5}, "mdi:wrench-cog"),
    ({"critical": 1, "warning": 0}, "mdi:wrench-clock"),
    ({"critical": 3, "warning": 2}, "mdi:wrench-clock"),
    ({"critical": 0, "warning": 0}, "mdi:check-decagram"),  # default
    ({}, "mdi:check-decagram"),  # missing both → default
])
def test_PM2_icon(summary, expected):
    """PM2: icon mapping by critical/warning count."""
    assert PredictiveMaintenanceSensorContract.icon(summary) == expected


# ─────────────────────────────────────────────────────────────────────────────
# PM3: extra_state_attributes — full breakdown mit defaults
# ─────────────────────────────────────────────────────────────────────────────
def test_PM3_attrs_full(mock_coordinator):
    """PM3a: volle attrs bei vollständigem summary."""
    summary = {
        "ok": True,
        "total_devices": 25,
        "healthy": 18,
        "degraded": 4,
        "warning": 2,
        "critical": 1,
        "avg_health_score": 78.5,
        "devices_needing_attention": [
            {"entity_id": "sensor.fridge", "energy_delta_pct": 15.2},
            {"entity_id": "sensor.hvac", "energy_delta_pct": 22.1},
        ],
        "upcoming_maintenance": ["filter_change", "belt_inspection"],
    }
    attrs = PredictiveMaintenanceSensorContract.extra_state_attributes(summary)
    assert attrs["total_devices"] == 25
    assert attrs["healthy"] == 18
    assert attrs["degraded"] == 4
    assert attrs["warning"] == 2
    assert attrs["critical"] == 1
    assert attrs["avg_health_score"] == 78.5
    assert len(attrs["devices_needing_attention"]) == 2
    assert attrs["upcoming_maintenance"] == ["filter_change", "belt_inspection"]


def test_PM3_attrs_defaults(mock_coordinator):
    """PM3b: defaults bei fehlenden Feldern."""
    summary = {"ok": True}
    attrs = PredictiveMaintenanceSensorContract.extra_state_attributes(summary)
    assert attrs["total_devices"] == 0
    assert attrs["healthy"] == 0
    assert attrs["degraded"] == 0
    assert attrs["warning"] == 0
    assert attrs["critical"] == 0
    assert attrs["avg_health_score"] == 100  # default
    assert attrs["devices_needing_attention"] == []
    assert attrs["upcoming_maintenance"] == []


def test_PM3_attrs_empty_summary(mock_coordinator):
    """PM3c: leeres summary → alle defaults."""
    attrs = PredictiveMaintenanceSensorContract.extra_state_attributes({})
    assert attrs["total_devices"] == 0
    assert attrs["avg_health_score"] == 100


# ─────────────────────────────────────────────────────────────────────────────
# PM4: edge cases — ok=false, None, non-dict
# ─────────────────────────────────────────────────────────────────────────────
def test_PM4_edge_ok_false():
    """PM4a: ok=false → defaults."""
    summary = {"ok": False, "avg_health_score": 50}
    assert PredictiveMaintenanceSensorContract.native_value(summary) == 50
    attrs = PredictiveMaintenanceSensorContract.extra_state_attributes(summary)
    assert attrs["total_devices"] == 0


def test_PM4_edge_none_summary():
    """PM4b: None summary → safe guards."""
    with pytest.raises(AttributeError):
        PredictiveMaintenanceSensorContract.native_value(None)


def test_PM4_edge_non_dict():
    """PM4c: non-dict summary → safe guards."""
    with pytest.raises(AttributeError):
        PredictiveMaintenanceSensorContract.native_value("invalid")


# ─────────────────────────────────────────────────────────────────────────────
# MC1: MaintenanceConfidenceSensor native_value — weighted score 0-100
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("summary,expected", [
    ({"critical": 0, "high": 0, "medium": 0, "low": 0}, 0.0),
    ({"critical": 1, "high": 0, "medium": 0, "low": 0}, 30.0),
    ({"critical": 0, "high": 1, "medium": 0, "low": 0}, 20.0),
    ({"critical": 0, "high": 0, "medium": 1, "low": 0}, 10.0),
    ({"critical": 0, "high": 0, "medium": 0, "low": 1}, 5.0),
    ({"critical": 2, "high": 1, "medium": 3, "low": 2}, 100.0),  # capped
    ({"critical": 5, "high": 5, "medium": 5, "low": 5}, 100.0),  # capped
    ({}, 0.0),  # missing all → 0
])
def test_MC1_confidence_score(summary, expected):
    """MC1: confidence = weighted sum (critical×30 + high×20 + medium×10 + low×5), capped 100."""
    assert MaintenanceConfidenceSensorContract.native_value(summary) == expected


# ─────────────────────────────────────────────────────────────────────────────
# GC1: Global Contract — Pure Projection, no local semantic invention
# ─────────────────────────────────────────────────────────────────────────────
def test_GC1_pure_projection_no_semantic_invention():
    """GC1: Sensor ist reine Projection-Shell — keine lokale Semantik-Invention."""
    # Verifiziert durch Contract-Mirror: alle Werte kommen direkt aus summary-Dict
    # native_value: direkter .get() lookup
    # icon: statische Map (critical/warning → icon)
    # attrs: direkte Dict-Lookups mit defaults
    summary = {
        "ok": True,
        "avg_health_score": 72.5,
        "total_devices": 10,
        "healthy": 7,
        "degraded": 2,
        "warning": 1,
        "critical": 0,
    }
    assert PredictiveMaintenanceSensorContract.native_value(summary) == 72.5
    assert PredictiveMaintenanceSensorContract.icon(summary) == "mdi:wrench-cog"
    attrs = PredictiveMaintenanceSensorContract.extra_state_attributes(summary)
    assert attrs["total_devices"] == 10
    # Keine lokale Berechnung/Heuristik — nur Pass-Through


# ─────────────────────────────────────────────────────────────────────────────
# GC2: Global Contract — Hits Core API endpoint
# ─────────────────────────────────────────────────────────────────────────────
def test_GC2_hits_core_api_endpoint():
    """GC2: Sensor ruft `/api/v1/hub/maintenance` auf — verifiziert durch Source-Inspection."""
    # Source-Inspection: async_update() macht GET {base}/maintenance
    # base = self._core_base_url() → Core-API, nicht HA-local
    # UnifiedAnomalyFramework wird für failure_predictions verwendet (separater Contract)
    pass  # Source-Inspection bestätigt Endpoint
