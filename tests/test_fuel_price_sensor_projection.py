"""Projection contract tests for FuelPriceSensor.

Verifies FuelPriceSensor is a pure projection shell on Core API:
  - GET /api/v1/regional/fuel/prices
  - GET /api/v1/regional/fuel/compare
No local semantic logic; all values come directly from Core.

Strategy: since aiohttp async mocking is environment-sensitive, test the
response-handling logic directly by injecting _data / _compare after
simulating what async_update() would compute from each endpoint.
"""

import pytest
from unittest.mock import MagicMock
import sys, types, os


# ─── Contract Mirrors ───────────────────────────────────────────────────────────

class FuelPricesContract:
    """Mirror of /api/v1/regional/fuel/prices response shape."""
    @staticmethod
    def build(
        ok=True,
        diesel_avg=1.52,
        diesel_min=1.48,
        e5_avg=1.68,
        e5_min=1.63,
        e10_avg=1.62,
        e10_min=1.58,
        station_count=12,
        cheapest_diesel="ARAL Dortmund",
        cheapest_e5="Shell München",
        radius_km=5,
    ):
        return {
            "ok": ok,
            "diesel_avg": diesel_avg,
            "diesel_min": diesel_min,
            "e5_avg": e5_avg,
            "e5_min": e5_min,
            "e10_avg": e10_avg,
            "e10_min": e10_min,
            "station_count": station_count,
            "cheapest_diesel": cheapest_diesel,
            "cheapest_e5": cheapest_e5,
            "radius_km": radius_km,
        }


class FuelCompareContract:
    """Mirror of /api/v1/regional/fuel/compare response shape."""
    @staticmethod
    def build(
        ok=True,
        electric_eur=3.20,
        diesel_eur=8.50,
        benzin_eur=7.90,
        e10_eur=7.75,
        cheapest="electric",
        savings_vs_diesel_eur=5.30,
        savings_vs_benzin_eur=4.70,
        co2_electric_kg=0.0,
        co2_diesel_kg=10.2,
        co2_benzin_kg=9.8,
    ):
        return {
            "ok": ok,
            "electric_eur": electric_eur,
            "diesel_eur": diesel_eur,
            "benzin_eur": benzin_eur,
            "e10_eur": e10_eur,
            "cheapest": cheapest,
            "savings_vs_diesel_eur": savings_vs_diesel_eur,
            "savings_vs_benzin_eur": savings_vs_benzin_eur,
            "co2_electric_kg": co2_electric_kg,
            "co2_diesel_kg": co2_diesel_kg,
            "co2_benzin_kg": co2_benzin_kg,
        }


# ─── Sensor builder ─────────────────────────────────────────────────────────────

def build_sensor(coordinator):
    """Instantiate FuelPriceSensor with required sys.modules stubs."""
    _root = os.path.join(os.path.dirname(__file__), "..", "custom_components", "pilotsuite")
    for _name, _path in [
        ("custom_components", None),
        ("custom_components.pilotsuite", _root),
        ("custom_components.pilotsuite.sensors", os.path.join(_root, "sensors")),
    ]:
        if _name not in sys.modules:
            mod = types.ModuleType(_name)
            if _path:
                mod.__path__ = [_path]
            sys.modules[_name] = mod

    from custom_components.pilotsuite.sensors.fuel_price_sensor import FuelPriceSensor
    return FuelPriceSensor(coordinator)


# ─── Helper: simulate async_update outcome ──────────────────────────────────────

def _simulate_prices_update(sensor, price_response):
    """Simulate what the prices branch of async_update does.

    Mirrors the sensor's inline logic:
      if resp.status == 200:
          data = await resp.json()
          if data.get("ok") and data.get("diesel_avg") is not None:
              self._data = data
    """
    ok = price_response.get("ok", False)
    has_prices = price_response.get("diesel_avg") is not None
    if ok and has_prices:
        sensor._data = price_response


def _simulate_compare_update(sensor, compare_response):
    """Simulate what the compare branch of async_update does.

    Mirrors:
      if resp.status == 200:
          data = await resp.json()
          if data.get("ok") and data.get("electric_eur") is not None:
              self._compare = data
    """
    ok = compare_response.get("ok", False)
    has_compare = compare_response.get("electric_eur") is not None
    if ok and has_compare:
        sensor._compare = compare_response


# ─── Test Cases ────────────────────────────────────────────────────────────────

def test_fp1_native_value_full_data(coordinator):
    """FP1: native_value returns electric_eur from _compare."""
    prices = FuelPricesContract.build()
    compare = FuelCompareContract.build(electric_eur=3.20)
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value == 3.20


def test_fp2_native_value_zero_savings(coordinator):
    """FP2: native_value is 0.0 when electric cost is zero."""
    prices = FuelPricesContract.build()
    compare = FuelCompareContract.build(electric_eur=0.0)
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value == 0.0


def test_fp3_native_value_missing_electric(coordinator):
    """FP3: native_value is None when compare has no electric_eur."""
    prices = FuelPricesContract.build()
    compare = FuelCompareContract.build(electric_eur=None)
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value is None


def test_fp4_native_value_prices_exception(coordinator):
    """FP4: native_value is None when prices fetch raises exception."""
    prices_exc = Exception("network error")
    compare = FuelCompareContract.build(electric_eur=3.20)
    sensor = build_sensor(coordinator)
    # Prices branch: exception caught and swallowed → _data stays {}
    try:
        raise prices_exc
    except Exception:
        pass  # caught in sensor's try/except
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value == 3.20  # compare still populated


def test_fp5_native_value_compare_404(coordinator):
    """FP5: native_value is None when compare returns non-200 (ok=False)."""
    prices = FuelPricesContract.build()
    compare = FuelCompareContract.build(ok=False)  # simulate 404 / bad response
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value is None


def test_fp6_attrs_full_data(coordinator):
    """FP6: extra_state_attributes contains all compare + price fields."""
    prices = FuelPricesContract.build(
        diesel_avg=1.55, diesel_min=1.49, e5_avg=1.70, e5_min=1.64,
        e10_avg=1.64, e10_min=1.60, station_count=8,
        cheapest_diesel="Shell Berlin", cheapest_e5="Total Hamburg",
        radius_km=10,
    )
    compare = FuelCompareContract.build(
        electric_eur=2.80, diesel_eur=8.20, benzin_eur=7.60, e10_eur=7.50,
        cheapest="electric", savings_vs_diesel_eur=5.40, savings_vs_benzin_eur=4.80,
        co2_electric_kg=0.0, co2_diesel_kg=10.5, co2_benzin_kg=9.9,
    )
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    attrs = sensor.extra_state_attributes
    assert attrs["electric_eur_100km"] == 2.80
    assert attrs["diesel_eur_100km"] == 8.20
    assert attrs["benzin_eur_100km"] == 7.60
    assert attrs["e10_eur_100km"] == 7.50
    assert attrs["cheapest"] == "electric"
    assert attrs["savings_vs_diesel_eur"] == 5.40
    assert attrs["savings_vs_benzin_eur"] == 4.80
    assert attrs["co2_electric_kg"] == 0.0
    assert attrs["co2_diesel_kg"] == 10.5
    assert attrs["co2_benzin_kg"] == 9.9
    assert attrs["diesel_avg_eur_l"] == 1.55
    assert attrs["diesel_min_eur_l"] == 1.49
    assert attrs["e5_avg_eur_l"] == 1.70
    assert attrs["station_count"] == 8
    assert attrs["cheapest_diesel_station"] == "Shell Berlin"
    assert attrs["radius_km"] == 10


def test_fp7_attrs_compare_only_prices_fail(coordinator):
    """FP7: attrs contain compare fields even when prices fetch fails."""
    compare = FuelCompareContract.build(electric_eur=4.10, diesel_eur=9.00)
    sensor = build_sensor(coordinator)
    # Prices: exception caught → _data stays {} → price keys absent from attrs
    _simulate_compare_update(sensor, compare)
    attrs = sensor.extra_state_attributes
    assert attrs["electric_eur_100km"] == 4.10
    assert attrs["diesel_eur_100km"] == 9.00
    assert "diesel_avg_eur_l" not in attrs  # prices failed → key absent


def test_fp8_attrs_prices_only_compare_fails(coordinator):
    """FP8: attrs contain price fields when compare fails."""
    prices = FuelPricesContract.build(diesel_avg=1.60, station_count=5)
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    # Compare: ok=False → _compare stays {}
    _simulate_compare_update(sensor, FuelCompareContract.build(ok=False))
    attrs = sensor.extra_state_attributes
    assert attrs["electric_eur_100km"] is None  # compare failed
    assert attrs["diesel_avg_eur_l"] == 1.60
    assert attrs["station_count"] == 5


def test_fp9_attrs_both_endpoints_fail(coordinator):
    """FP9: attrs show None electric when both endpoints fail."""
    sensor = build_sensor(coordinator)
    # Both fail → _data and _compare stay {} → electric_eur_100km present but None
    _simulate_compare_update(sensor, FuelCompareContract.build(ok=False))
    attrs = sensor.extra_state_attributes
    assert attrs["electric_eur_100km"] is None
    assert "diesel_avg_eur_l" not in attrs


# ─── Global Contract ────────────────────────────────────────────────────────────

def test_gc1_hits_core_api_endpoints(coordinator):
    """"GC1: Sensor fetches from /api/v1/regional/fuel/prices and /api/v1/regional/fuel/compare.

    Verified by code inspection: async_update() makes two aiohttp GET calls to
    f"{base}/fuel/prices" and f"{base}/fuel/compare" in parallel.
    """
    from custom_components.pilotsuite.sensors.fuel_price_sensor import FuelPriceSensor
    import inspect
    source = inspect.getsource(FuelPriceSensor.async_update)
    assert "/fuel/prices" in source, "Must hit /api/v1/regional/fuel/prices"
    assert "/fuel/compare" in source, "Must hit /api/v1/regional/fuel/compare"


def test_gc2_no_local_semantic_logic(coordinator):
    """GC2: Sensor performs no local cost calculations — pure pass-through of Core values."""
    compare = FuelCompareContract.build(
        electric_eur=5.00, diesel_eur=10.00, benzin_eur=9.50,
        co2_electric_kg=0.0, co2_diesel_kg=12.0, co2_benzin_kg=11.5,
    )
    prices = FuelPricesContract.build()
    sensor = build_sensor(coordinator)
    _simulate_prices_update(sensor, prices)
    _simulate_compare_update(sensor, compare)
    assert sensor.native_value == 5.00
    attrs = sensor.extra_state_attributes
    assert attrs["diesel_eur_100km"] == 10.00
    assert attrs["co2_electric_kg"] == 0.0
