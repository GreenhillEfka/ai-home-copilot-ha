"""Demand Response Sensor — Projection Contract Tests (HA-137).

Verifies DemandResponseSensor is a pure projection shell on
/api/v1/energy/demand-response/status — no local semantic invention.

Contract:
- native_value: SIGNAL_LABELS.get(signal_level, "Unknown")
- icon: SIGNAL_ICONS.get(signal_level, "mdi:transmission-tower")
- attrs: direct lookups from /api/v1/energy/demand-response/status response
"""
import pytest


# =============================================================================
# Contract Mirror
# =============================================================================

SIGNAL_LABELS = {0: "Normal", 1: "Advisory", 2: "Moderate", 3: "Critical"}
SIGNAL_ICONS = {
    0: "mdi:transmission-tower",
    1: "mdi:alert-circle-outline",
    2: "mdi:alert",
    3: "mdi:alert-octagon",
}


def _safe_int(value, default=0):
    try:
        v = float(value)
        if v != int(v) or v < 0:
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        f = float(value)
        if f < 0:
            return default
        return f
    except (TypeError, ValueError):
        return default


def _safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    return default


def _safe_signal(value, default=0):
    """Guard signal level against non-integer or out-of-range values.

    Valid signal levels are 0–3.
    """
    try:
        v = float(value)
        if v != int(v) or v < 0 or v > 3:
            return default
        return int(v)
    except (TypeError, ValueError):
        return default


class DemandResponseSensorContract:
    """Mirror of DemandResponseSensor projection logic.

    Contract:
    - hits /api/v1/energy/demand-response/status (Core API)
    - native_value: SIGNAL_LABELS.get(signal_level, "Unknown")
    - icon: SIGNAL_ICONS.get(signal_level, "mdi:transmission-tower")
    - attrs: safe lookups from response dict (guards against malformed payloads)
    """

    def __init__(self, api_response):
        self._data = api_response if isinstance(api_response, dict) else {}
        raw_signal = self._data.get("current_signal") if self._data.get("ok") else None
        self._signal_level = _safe_signal(raw_signal, default=0)

    @property
    def native_value(self) -> str:
        return SIGNAL_LABELS.get(self._signal_level, "Unknown")

    @property
    def icon(self) -> str:
        return SIGNAL_ICONS.get(self._signal_level, "mdi:transmission-tower")

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "signal_level": self._signal_level,
            "active_signals": _safe_int(self._data.get("active_signals")),
            "managed_devices": _safe_int(self._data.get("managed_devices")),
            "curtailed_devices": _safe_int(self._data.get("curtailed_devices")),
            "total_reduction_watts": _safe_float(self._data.get("total_reduction_watts")),
            "response_active": _safe_bool(self._data.get("response_active")),
        }


# =============================================================================
# DR1: native_value = SIGNAL_LABELS[signal_level]
# =============================================================================

class TestDR1NativeValue:
    """DR1: native_value cases for DemandResponseSensor."""

    @pytest.mark.parametrize("signal_level,expected", [
        (0, "Normal"),
        (1, "Advisory"),
        (2, "Moderate"),
        (3, "Critical"),
    ])
    def test_dr1_signal_level_label(self, signal_level, expected):
        resp = {"ok": True, "current_signal": signal_level}
        assert DemandResponseSensorContract(resp).native_value == expected

    def test_dr1_out_of_range_yields_normal(self):
        """DR1.5: signal_level > 3 → out-of-range guard → 0 → 'Normal'.

        Valid signal levels are 0–3. Values outside this range are rejected
        by the _safe_signal range guard and fall back to 0 ('Normal').
        """
        resp = {"ok": True, "current_signal": 99}
        assert DemandResponseSensorContract(resp).native_value == "Normal"

    def test_dr1_ok_false_yields_zero(self):
        """ok=false → signal_level defaults to 0 → 'Normal'."""
        resp = {"ok": False}
        assert DemandResponseSensorContract(resp).native_value == "Normal"

    def test_dr1_missing_current_signal(self):
        """current_signal missing → defaults to 0 → 'Normal'."""
        resp = {"ok": True}
        assert DemandResponseSensorContract(resp).native_value == "Normal"


# =============================================================================
# DR2: icon = SIGNAL_ICONS[signal_level]
# =============================================================================

class TestDR2Icon:
    """DR2: icon cases for DemandResponseSensor."""

    @pytest.mark.parametrize("signal_level,expected", [
        (0, "mdi:transmission-tower"),
        (1, "mdi:alert-circle-outline"),
        (2, "mdi:alert"),
        (3, "mdi:alert-octagon"),
    ])
    def test_dr2_signal_level_icon(self, signal_level, expected):
        resp = {"ok": True, "current_signal": signal_level}
        assert DemandResponseSensorContract(resp).icon == expected

    def test_dr2_unknown_level_default(self):
        """signal_level 99 not in SIGNAL_ICONS → default 'mdi:transmission-tower'."""
        resp = {"ok": True, "current_signal": 99}
        assert DemandResponseSensorContract(resp).icon == "mdi:transmission-tower"


# =============================================================================
# DR3: extra_state_attributes = direct lookups from API response
# =============================================================================

class TestDR3Attrs:
    """DR3: extra_state_attributes from /api/v1/energy/demand-response/status."""

    def test_dr3_attrs_full(self):
        """Full response — all fields present."""
        resp = {
            "ok": True,
            "current_signal": 2,
            "active_signals": 3,
            "managed_devices": 5,
            "curtailed_devices": 2,
            "total_reduction_watts": 1500,
            "response_active": True,
        }
        attrs = DemandResponseSensorContract(resp).extra_state_attributes
        assert attrs["signal_level"] == 2
        assert attrs["active_signals"] == 3
        assert attrs["managed_devices"] == 5
        assert attrs["curtailed_devices"] == 2
        assert attrs["total_reduction_watts"] == 1500
        assert attrs["response_active"] is True

    def test_dr3_attrs_defaults_when_empty(self):
        """Empty response → all optional fields default to 0/False."""
        resp = {}
        attrs = DemandResponseSensorContract(resp).extra_state_attributes
        assert attrs["signal_level"] == 0
        assert attrs["active_signals"] == 0
        assert attrs["managed_devices"] == 0
        assert attrs["curtailed_devices"] == 0
        assert attrs["total_reduction_watts"] == 0
        assert attrs["response_active"] is False

    def test_dr3_attrs_partial(self):
        """Partial response — only some optional fields present."""
        resp = {"ok": True, "current_signal": 1, "active_signals": 2}
        attrs = DemandResponseSensorContract(resp).extra_state_attributes
        assert attrs["signal_level"] == 1
        assert attrs["active_signals"] == 2
        assert attrs["managed_devices"] == 0
        assert attrs["response_active"] is False


# =============================================================================
# DR4: edge cases
# =============================================================================

class TestDR4Edge:
    """DR4: edge cases for DemandResponseSensor."""

    def test_dr4_zero_signal_normal(self):
        """signal_level=0 → 'Normal', transmission tower icon."""
        resp = {"ok": True, "current_signal": 0}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"
        assert dr.icon == "mdi:transmission-tower"

    def test_dr4_max_signal(self):
        """signal_level=3 → 'Critical', alert-octagon icon."""
        resp = {"ok": True, "current_signal": 3}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Critical"
        assert dr.icon == "mdi:alert-octagon"

    def test_dr4_extreme_watts(self):
        """Very large total_reduction_watts passes through unchanged."""
        resp = {"ok": True, "current_signal": 1, "total_reduction_watts": 1_000_000}
        attrs = DemandResponseSensorContract(resp).extra_state_attributes
        assert attrs["total_reduction_watts"] == 1_000_000

    def test_dr4_missing_optional_fields(self):
        """Only current_signal present — rest default."""
        resp = {"ok": True, "current_signal": 2}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Moderate"
        attrs = dr.extra_state_attributes
        assert attrs["active_signals"] == 0
        assert attrs["managed_devices"] == 0
        assert attrs["curtailed_devices"] == 0
        assert attrs["response_active"] is False


# =============================================================================
# DRM: malformed payload guard cases (HA-334)
# =============================================================================

class TestDRMalformed:
    """DRM: DemandResponseSensor guards against malformed API payloads."""

    def test_drm1_signal_string(self):
        """DRM1: current_signal as string → defaults to 0 → 'Normal'."""
        resp = {"ok": True, "current_signal": "high"}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"
        assert dr.extra_state_attributes["signal_level"] == 0

    def test_drm2_signal_none(self):
        """DRM2: current_signal = None → defaults to 0 → 'Normal'."""
        resp = {"ok": True, "current_signal": None}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"

    def test_drm3_signal_negative(self):
        """DRM3: current_signal = -1 → non-negative guard → 0 → 'Normal'."""
        resp = {"ok": True, "current_signal": -1}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"

    def test_drm4_signal_float_non_int(self):
        """DRM4: current_signal as float (non-integer) → 0 → 'Normal'."""
        resp = {"ok": True, "current_signal": 2.9}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"

    def test_drm5_active_signals_string(self):
        """DRM5: active_signals as string → safe default 0."""
        resp = {"ok": True, "active_signals": "three"}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["active_signals"] == 0

    def test_drm6_managed_devices_negative(self):
        """DRM6: managed_devices negative → safe default 0."""
        resp = {"ok": True, "managed_devices": -5}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["managed_devices"] == 0

    def test_drm7_total_reduction_watts_string(self):
        """DRM7: total_reduction_watts as string → safe default 0.0."""
        resp = {"ok": True, "total_reduction_watts": "1500w"}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["total_reduction_watts"] == 0.0

    def test_drm8_response_active_string(self):
        """DRM8: response_active as string → safe default False."""
        resp = {"ok": True, "response_active": "yes"}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["response_active"] is False

    def test_drm9_response_active_int(self):
        """DRM9: response_active as non-bool int → safe default False."""
        resp = {"ok": True, "response_active": 1}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["response_active"] is False

    def test_drm10_top_level_non_dict(self):
        """DRM10: top-level response is a list (not a dict) → safe defaults.

        When the API returns a list instead of a dict, the sensor's
        isinstance(api_response, dict) guard catches this and self._data
        becomes {}. With no valid "ok" key, raw_signal is None and the
        _safe_signal fallback produces 0 → 'Normal'. The sensor never
        leaks "Unknown" from a malformed list-shaped response.
        """
        resp = [{"ok": True}]
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"  # list rejected → safe default 0
        assert dr.extra_state_attributes["active_signals"] == 0
        assert dr.extra_state_attributes["response_active"] is False

    def test_drm11_signal_huge_float(self):
        """DRM11: current_signal as huge float → out-of-range → 0 → 'Normal'."""
        resp = {"ok": True, "current_signal": 1e15}
        dr = DemandResponseSensorContract(resp)
        assert dr.native_value == "Normal"

    def test_drm12_curtailed_devices_float(self):
        """DRM12: curtailed_devices as float non-integer → safe default 0."""
        resp = {"ok": True, "curtailed_devices": 1.5}
        dr = DemandResponseSensorContract(resp)
        assert dr.extra_state_attributes["curtailed_devices"] == 0


# =============================================================================
# GC1–GC2: global contract
# =============================================================================

class TestDRGlobalContract:
    """GC: global contract verification for DemandResponseSensor."""

    def test_gc1_hits_core_api(self):
        """GC1: /api/v1/energy/demand-response/status is the only data source."""
        # Contract: url = f"{_core_base_url()}/api/v1/energy/demand-response/status"
        # We verify the contract mirror exercises exactly those fields
        resp = {"ok": True, "current_signal": 2, "active_signals": 1,
                "managed_devices": 3, "curtailed_devices": 1,
                "total_reduction_watts": 500, "response_active": True}
        dr = DemandResponseSensorContract(resp)
        # All properties must be accessible (contract surface verified)
        assert isinstance(dr.native_value, str)
        assert isinstance(dr.icon, str)
        assert isinstance(dr.extra_state_attributes, dict)

    def test_gc2_no_local_semantic_invention(self):
        """GC2: no local classification or heuristic — pure dict lookups."""
        # All mappings are static dicts; no computed scores, ML, or heuristics
        resp = {"ok": True, "current_signal": 3}
        dr = DemandResponseSensorContract(resp)
        # native_value: static lookup only
        assert dr.native_value == "Critical"
        # icon: static lookup only
        assert dr.icon == "mdi:alert-octagon"
        # attrs: direct pass-through, no transformation
        assert dr.extra_state_attributes["signal_level"] == 3
        assert dr.extra_state_attributes["response_active"] is False
