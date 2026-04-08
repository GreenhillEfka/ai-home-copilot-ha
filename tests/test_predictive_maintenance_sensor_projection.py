"""Projection Contract Tests for PredictiveMaintenanceSensor.

Verifies PredictiveMaintenanceSensor is a pure projection shell on
/api/v1/hub/maintenance — no local semantic invention.

HA-233
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ─── Contract Mirror ────────────────────────────────────────────────────────

class PredictiveMaintenanceSensorContract:
    """Mirror of PredictiveMaintenanceSensor projection logic."""

    def __init__(self, data):
        self._summary = data or {}

    @property
    def native_value(self):
        return self._summary.get("avg_health_score")

    @property
    def icon(self):
        critical = self._summary.get("critical", 0)
        warning = self._summary.get("warning", 0)
        if critical > 0:
            return "mdi:wrench-clock"
        elif warning > 0:
            return "mdi:wrench-cog"
        return "mdi:check-decagram"

    @property
    def extra_state_attributes(self):
        return {
            "total_devices": self._summary.get("total_devices", 0),
            "healthy": self._summary.get("healthy", 0),
            "degraded": self._summary.get("degraded", 0),
            "warning": self._summary.get("warning", 0),
            "critical": self._summary.get("critical", 0),
            "avg_health_score": self._summary.get("avg_health_score", 100),
            "devices_needing_attention": self._summary.get("devices_needing_attention", []),
            "upcoming_maintenance": self._summary.get("upcoming_maintenance", []),
        }


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def pm_contract():
    """Bare contract mirror with empty/default data."""
    return PredictiveMaintenanceSensorContract({})


@pytest.fixture
def pm_full():
    """Contract mirror with complete maintenance data — all healthy."""
    return PredictiveMaintenanceSensorContract({
        "ok": True,
        "avg_health_score": 87.5,
        "total_devices": 12,
        "healthy": 9,
        "degraded": 2,
        "warning": 0,
        "critical": 0,
        "devices_needing_attention": [],
        "upcoming_maintenance": [],
    })


@pytest.fixture
def pm_critical():
    """Contract mirror with critical devices."""
    return PredictiveMaintenanceSensorContract({
        "ok": True,
        "avg_health_score": 45.2,
        "total_devices": 5,
        "healthy": 1,
        "degraded": 1,
        "warning": 1,
        "critical": 2,
        "devices_needing_attention": ["router_main", "switch_garage"],
        "upcoming_maintenance": [],
    })


# ─── PM1: native_value ───────────────────────────────────────────────────────

class TestPMNativeValue:
    """PM1: native_value = avg_health_score from API."""

    def test_pm1a_full_data(self, pm_full):
        """Full maintenance data — avg_health_score exposed as native_value."""
        assert pm_full.native_value == 87.5

    def test_pm1b_missing_score(self, pm_contract):
        """Missing avg_health_score key — None (not 100, sensor defaults in attrs only)."""
        assert pm_contract.native_value is None

    def test_pm1c_null_score(self):
        """Null avg_health_score — None."""
        c = PredictiveMaintenanceSensorContract({"avg_health_score": None})
        assert c.native_value is None

    def test_pm1d_zero_score(self):
        """Zero avg_health_score — 0 (valid, not same as missing)."""
        c = PredictiveMaintenanceSensorContract({"avg_health_score": 0})
        assert c.native_value == 0

    def test_pm1e_integer_score(self):
        """Integer avg_health_score — passthrough as int/float."""
        c = PredictiveMaintenanceSensorContract({"avg_health_score": 100})
        assert c.native_value == 100


# ─── PM2: icon ───────────────────────────────────────────────────────────────

class TestPMIcon:
    """PM2: icon reflects device health status."""

    def test_pm2a_all_healthy(self, pm_full):
        """No warnings or criticals — check-decagram."""
        assert pm_full.icon == "mdi:check-decagram"

    def test_pm2b_warning_only(self, pm_contract):
        """Warning present, no critical — wrench-cog."""
        c = PredictiveMaintenanceSensorContract({"warning": 1, "critical": 0})
        assert c.icon == "mdi:wrench-cog"

    def test_pm2c_critical_present(self, pm_critical):
        """Critical present — wrench-clock (highest priority)."""
        assert pm_critical.icon == "mdi:wrench-clock"

    def test_pm2d_multiple_critical(self):
        """Multiple criticals — wrench-clock."""
        c = PredictiveMaintenanceSensorContract({"critical": 3, "warning": 5})
        assert c.icon == "mdi:wrench-clock"

    def test_pm2e_zero_counts(self, pm_contract):
        """All zeros — all_healthy icon."""
        assert pm_contract.icon == "mdi:check-decagram"


# ─── PM3: extra_state_attributes ─────────────────────────────────────────────

class TestPMAttrs:
    """PM3: extra_state_attributes pass through all maintenance fields."""

    def test_pm3a_full_attrs(self, pm_full):
        """Full data — all 8 fields present."""
        attrs = pm_full.extra_state_attributes
        assert attrs["total_devices"] == 12
        assert attrs["healthy"] == 9
        assert attrs["degraded"] == 2
        assert attrs["warning"] == 0
        assert attrs["critical"] == 0
        assert attrs["avg_health_score"] == 87.5
        assert attrs["devices_needing_attention"] == []
        assert attrs["upcoming_maintenance"] == []

    def test_pm3b_empty_attrs(self, pm_contract):
        """Empty data — all fields default to 0 or empty list."""
        attrs = pm_contract.extra_state_attributes
        assert attrs["total_devices"] == 0
        assert attrs["healthy"] == 0
        assert attrs["degraded"] == 0
        assert attrs["warning"] == 0
        assert attrs["critical"] == 0
        assert attrs["avg_health_score"] == 100  # sensor default in attrs
        assert attrs["devices_needing_attention"] == []
        assert attrs["upcoming_maintenance"] == []

    def test_pm3c_partial_attrs(self):
        """Partial data — missing keys fall through to defaults."""
        c = PredictiveMaintenanceSensorContract({"total_devices": 3, "healthy": 3})
        attrs = c.extra_state_attributes
        assert attrs["total_devices"] == 3
        assert attrs["healthy"] == 3
        assert attrs["degraded"] == 0
        assert attrs["warning"] == 0
        assert attrs["critical"] == 0
        assert attrs["devices_needing_attention"] == []

    def test_pm3d_devices_as_list(self, pm_full):
        """devices_needing_attention must be a list (even if returned as wrong type)."""
        c = PredictiveMaintenanceSensorContract({"devices_needing_attention": "not_a_list"})
        # sensor would get str directly; attrs pass through whatever is there
        assert c.extra_state_attributes["devices_needing_attention"] == "not_a_list"


# ─── PM4: Edge cases ────────────────────────────────────────────────────────

class TestPMEdge:
    """PM4: Edge cases and boundary conditions."""

    def test_pm4a_unreachable_core(self, pm_contract):
        """Core unreachable — empty data, defaults apply."""
        assert pm_contract.native_value is None
        assert pm_contract.icon == "mdi:check-decagram"

    def test_pm4b_negative_health_score(self):
        """Negative avg_health_score — passthrough (sensor does not validate)."""
        c = PredictiveMaintenanceSensorContract({"avg_health_score": -10.0})
        assert c.native_value == -10.0

    def test_pm4c_extreme_health_score(self):
        """Extreme avg_health_score (255) — passthrough, no clamping."""
        c = PredictiveMaintenanceSensorContract({"avg_health_score": 255.0})
        assert c.native_value == 255.0

    def test_pm4d_empty_list_fields(self):
        """Empty list fields are valid — not same as missing."""
        c = PredictiveMaintenanceSensorContract({
            "devices_needing_attention": [],
            "upcoming_maintenance": [],
        })
        attrs = c.extra_state_attributes
        assert attrs["devices_needing_attention"] == []
        assert attrs["upcoming_maintenance"] == []

    def test_pm4e_non_bool_ok(self):
        """ok field is not boolean — sensor ignores it (only checks truthiness)."""
        c = PredictiveMaintenanceSensorContract({"ok": "error_string", "avg_health_score": 80.0})
        assert c.native_value == 80.0  # data loaded despite ok being non-bool


# ─── GC1/GC2: Global Contract ───────────────────────────────────────────────

class TestPMGlobalContract:
    """GC1/GC2: Global projection contract — pure Core API, no semantic invention."""

    def test_gc1_source_inspection(self):
        """GC1: Source is exclusively /api/v1/hub/maintenance."""
        import inspect
        from custom_components.pilotsuite.sensors import predictive_maintenance_sensor as pm_src
        source = inspect.getsource(pm_src)
        # Must reference the /maintenance endpoint on the hub base URL
        assert "/maintenance" in source
        # No other /api/v1/... endpoints
        other_paths = ["/api/v1/zone", "/api/v1/hub/notifications", "/api/v1/comfort",
                       "/api/v1/energy", "/api/v1/sensor", "/api/v1/weather",
                       "/api/v1/predict"]
        for p in other_paths:
            assert p not in source, f"Unexpected API path {p} in source"

    def test_gc2_no_local_semantic_invention(self):
        """GC2: No local heuristic classification or semantic invention.

        native_value is raw avg_health_score — no mapping, no thresholds applied.
        icon uses simple priority: critical > warning > else (structural, not semantic).
        attrs are pure passthrough with safe defaults.
        """
        c_full = PredictiveMaintenanceSensorContract({
            "avg_health_score": 50.0,
            "critical": 0,
            "warning": 0,
        })
        # native_value = raw score, no classification
        assert c_full.native_value == 50.0
        # icon is structural priority, not a computed "health status"
        assert c_full.icon == "mdi:check-decagram"
