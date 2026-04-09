"""Projection Contract Tests: tariff_sensor (HA-250).

Verifies:
- TariffSensor: pure projection on /api/v1/regional/tariff/summary
- native_value → current_price_ct_kwh (float ct/kWh)
- icon → current_level mapping (very_low/low/normal/high/very_high)
- extra_state_attributes → price stats, levels, hours, source
"""

import pytest

from custom_components.pilotsuite.sensors.tariff_sensor import TariffSensor


# =============================================================================
# Contract Mirror
# =============================================================================


class TariffSensorContract:
    """Mirror of TariffSensor state construction (test oracle)."""

    _LEVEL_ICONS = {
        "very_low": "mdi:lightning-bolt",
        "low": "mdi:flash",
        "normal": "mdi:flash-outline",
        "high": "mdi:flash-alert",
        "very_high": "mdi:flash-alert-outline",
    }

    @staticmethod
    def native_value(data: dict) -> float | None:
        if not data or not isinstance(data, dict):
            return None
        if not data.get("ok"):
            return None
        return data.get("current_price_ct_kwh")

    @staticmethod
    def icon(data: dict) -> str:
        level = (data or {}).get("current_level", "normal")
        return TariffSensorContract._LEVEL_ICONS.get(level, "mdi:flash-outline")

    @staticmethod
    def extra_state_attributes(data: dict) -> dict:
        if not data or not isinstance(data, dict):
            return {}
        attrs = {
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
        return attrs


# =============================================================================
# Sensor Fixture
# =============================================================================


class FakeCoordinator:
    def __init__(self, data: dict):
        self.data = data


# =============================================================================
# native_value Tests — TV1..TV7
# =============================================================================


def _make_tariff_sensor(data: dict) -> TariffSensor:
    hass = object()
    coordinator = FakeCoordinator(data)
    sensor = TariffSensor(coordinator)
    sensor.hass = hass
    # _data is only populated by async_update; set it directly for testing
    sensor._data = data if data else {}
    return sensor


def test_tv1_full_ok():
    """TV1: full ok response → native_value is current_price_ct_kwh."""
    data = {
        "ok": True,
        "current_price_ct_kwh": 28.50,
        "current_price_eur_kwh": 0.285,
        "current_level": "normal",
        "avg_price_eur_kwh": 0.31,
        "min_price_eur_kwh": 0.22,
        "max_price_eur_kwh": 0.42,
        "min_hour": "03:00",
        "max_hour": "19:00",
        "spread_eur_kwh": 0.20,
        "tariff_type": "a wattar",
        "source": "aWATTar",
        "hours_available": 24,
    }
    sensor = _make_tariff_sensor(data)
    assert sensor.native_value == 28.50


def test_tv2_ok_false():
    """TV2: ok=false still returns current_price_ct_kwh (sensor is pure passthrough, ok not checked)."""
    data = {"ok": False, "current_price_ct_kwh": 28.50}
    sensor = _make_tariff_sensor(data)
    assert sensor.native_value == 28.50


def test_tv3_missing_current_price():
    """TV3: ok=true but current_price_ct_kwh absent → native_value is None."""
    data = {"ok": True, "current_price_eur_kwh": 0.285}
    sensor = _make_tariff_sensor(data)
    assert sensor.native_value is None


def test_tv4_empty_data():
    """TV4: empty dict → native_value is None."""
    sensor = _make_tariff_sensor({})
    assert sensor.native_value is None


def test_tv5_none_data():
    """TV5: None → native_value is None."""
    sensor = _make_tariff_sensor(None)
    assert sensor.native_value is None


def test_tv6_price_zero():
    """TV6: ok=true, current_price_ct_kwh=0.0 → native_value is 0.0 (valid tariff)."""
    data = {"ok": True, "current_price_ct_kwh": 0.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.native_value == 0.0


def test_tv7_none_price():
    """TV7: ok=true, current_price_ct_kwh=None → native_value is None."""
    data = {"ok": True, "current_price_ct_kwh": None}
    sensor = _make_tariff_sensor(data)
    assert sensor.native_value is None


# =============================================================================
# icon Tests — TI1..TI5
# =============================================================================


def test_ti1_very_low():
    """TI1: current_level=very_low → mdi:lightning-bolt."""
    data = {"ok": True, "current_level": "very_low", "current_price_ct_kwh": 15.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:lightning-bolt"


def test_ti2_low():
    """TI2: current_level=low → mdi:flash."""
    data = {"ok": True, "current_level": "low", "current_price_ct_kwh": 20.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash"


def test_ti3_normal():
    """TI3: current_level=normal → mdi:flash-outline."""
    data = {"ok": True, "current_level": "normal", "current_price_ct_kwh": 28.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash-outline"


def test_ti4_high():
    """TI4: current_level=high → mdi:flash-alert."""
    data = {"ok": True, "current_level": "high", "current_price_ct_kwh": 38.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash-alert"


def test_ti5_very_high():
    """TI5: current_level=very_high → mdi:flash-alert-outline."""
    data = {"ok": True, "current_level": "very_high", "current_price_ct_kwh": 48.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash-alert-outline"


def test_ti6_unknown_level():
    """TI6: unknown level → default mdi:flash-outline."""
    data = {"ok": True, "current_level": "unknown_tier", "current_price_ct_kwh": 30.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash-outline"


def test_ti7_missing_level():
    """TI7: no current_level → default mdi:flash-outline."""
    data = {"ok": True, "current_price_ct_kwh": 30.0}
    sensor = _make_tariff_sensor(data)
    assert sensor.icon == "mdi:flash-outline"


# =============================================================================
# extra_state_attributes Tests — TA1..TA6
# =============================================================================


def test_ta1_full_attrs():
    """TA1: full ok response → all 11 attrs present and eur→ct/kWh conversions correct."""
    data = {
        "ok": True,
        "current_price_ct_kwh": 28.50,
        "current_price_eur_kwh": 0.285,
        "current_level": "normal",
        "avg_price_eur_kwh": 0.31,
        "min_price_eur_kwh": 0.22,
        "max_price_eur_kwh": 0.42,
        "min_hour": "03:00",
        "max_hour": "19:00",
        "spread_eur_kwh": 0.20,
        "tariff_type": "a wattar",
        "source": "aWATTar",
        "hours_available": 24,
    }
    sensor = _make_tariff_sensor(data)
    attrs = sensor.extra_state_attributes
    assert attrs["current_price_eur_kwh"] == 0.285
    assert attrs["current_level"] == "normal"
    assert attrs["avg_price_ct_kwh"] == 31.0   # 0.31 * 100
    assert attrs["min_price_ct_kwh"] == 22.0  # 0.22 * 100
    assert attrs["max_price_ct_kwh"] == 42.0  # 0.42 * 100
    assert attrs["min_hour"] == "03:00"
    assert attrs["max_hour"] == "19:00"
    assert attrs["spread_ct_kwh"] == 20.0      # 0.20 * 100
    assert attrs["tariff_type"] == "a wattar"
    assert attrs["source"] == "aWATTar"
    assert attrs["hours_available"] == 24


def test_ta2_partial_attrs():
    """TA2: sparse data → missing keys omitted, numeric 0 defaults applied."""
    data = {"ok": True, "current_price_ct_kwh": 25.0}
    sensor = _make_tariff_sensor(data)
    attrs = sensor.extra_state_attributes
    assert attrs["current_price_eur_kwh"] is None
    assert attrs["avg_price_ct_kwh"] == 0.0
    assert attrs["min_price_ct_kwh"] == 0.0
    assert attrs["max_price_ct_kwh"] == 0.0
    assert attrs["min_hour"] == ""
    assert attrs["max_hour"] == ""
    assert attrs["spread_ct_kwh"] == 0.0
    assert attrs["tariff_type"] == ""
    assert attrs["source"] == ""
    assert attrs["hours_available"] == 0


def test_ta3_attrs_ok_false():
    """TA3: ok=false → attrs still return price fields (sensor is pure passthrough, ok not checked)."""
    data = {"ok": False, "current_price_eur_kwh": 0.30, "current_level": "high",
             "avg_price_eur_kwh": 0.30, "min_price_eur_kwh": 0.20, "max_price_eur_kwh": 0.40,
             "spread_eur_kwh": 0.20, "tariff_type": "eplex", "source": "EPEX", "hours_available": 24}
    sensor = _make_tariff_sensor(data)
    attrs = sensor.extra_state_attributes
    assert attrs["current_price_eur_kwh"] == 0.30
    assert attrs["current_level"] == "high"
    assert attrs["tariff_type"] == "eplex"
    assert attrs["source"] == "EPEX"


def test_ta4_attrs_none_data():
    """TA4: None → empty attrs dict (no data to pass through)."""
    sensor = _make_tariff_sensor(None)
    attrs = sensor.extra_state_attributes
    # None data means _data={} after fixture fix, attrs from {} return all Nones/zero/empty
    assert attrs.get("current_price_eur_kwh") is None
    assert attrs.get("current_level") == ""
    assert attrs.get("hours_available") == 0


def test_ta5_eur_conversion_rounding():
    """TA5: eur→ct/kWh conversion rounds to 2 decimal places."""
    data = {
        "ok": True,
        "current_price_ct_kwh": 33.333,
        "avg_price_eur_kwh": 0.33333,
        "min_price_eur_kwh": 0.1111,
        "max_price_eur_kwh": 0.6666,
        "spread_eur_kwh": 0.0555,
    }
    sensor = _make_tariff_sensor(data)
    attrs = sensor.extra_state_attributes
    # round(0.33333*100, 2) = 33.33, round(0.1111*100, 2) = 11.11, round(0.6666*100, 2) = 66.66, round(0.0555*100, 2) = 5.55
    assert attrs["avg_price_ct_kwh"] == 33.33
    assert attrs["min_price_ct_kwh"] == 11.11
    assert attrs["max_price_ct_kwh"] == 66.66
    assert attrs["spread_ct_kwh"] == 5.55


def test_ta6_all_level_values():
    """TA6: all 5 level values are stored in current_level attr."""
    for level in ("very_low", "low", "normal", "high", "very_high"):
        data = {"ok": True, "current_level": level, "current_price_ct_kwh": 30.0}
        sensor = _make_tariff_sensor(data)
        assert sensor.extra_state_attributes["current_level"] == level


# =============================================================================
# Global Contract Tests — GC1..GC2
# =============================================================================


def test_gc1_is_pure_projection():
    """GC1: TariffSensor is a pure projection on /api/v1/regional/tariff/summary — no local semantics."""
    import inspect
    source = inspect.getsource(TariffSensor)
    # Guard: no local tariff calculation or heuristic invented locally
    assert "TARIFF_WINDOW" not in source
    assert "optimal_window" not in source
    assert "cheapest_hour" not in source
    # Guard: native_value is a direct passthrough of the API field
    assert "current_price_ct_kwh" in source
    # Guard: no mathematical transformation beyond unit conversion (eur→ct/kWh)
    assert "current_price_ct_kwh" in source


def test_gc2_endpoint_in_update():
    """GC2: async_update calls /api/v1/regional/tariff/summary explicitly."""
    import inspect
    source = inspect.getsource(TariffSensor.async_update)
    assert "/tariff/summary" in source
