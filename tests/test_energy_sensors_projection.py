"""EnergyProxySensor Projection-Contract-Tests.

Contract: EnergyProxySensor ist HA-lokale Projection-Shell auf hass.states.async_all()
- power sensors (device_class="power") → total_power_w Aggregation
- lights + switches → active device count
- Threshold-Logik: <100W name="low, &lt;500W=moderate, &lt;1500W=high, ">=1500W=very_high
- Frugality-Score: inverse consumption (0.0-1.0, 1.0=most frugal)
- Keine lokale Semantik — reine State-Aggregation + Schwellenwerte

HA-174: energy_sensors.py Projection-Contract-Tests (22 Cases)
"""
import pytest
from typing import Any

from custom_components.pilotsuite.sensors.energy_sensors import (
    EnergyProxySensor,
    EnergyUsageLevel,
    FrugalityScore,
    _POWER_THRESHOLD_LOW,
    _POWER_THRESHOLD_MODERATE,
    _POWER_THRESHOLD_HIGH,
    _POWER_MAX_NORMAL,
)


# ─────────────────────────────────────────────────────────────────────────────
# Contract-Mirror: lokale Kopie der Sensor-Logik für Test-Assertions
# ─────────────────────────────────────────────────────────────────────────────

class EnergyUsageLevelMirror:
    """Mirror of EnergyUsageLevel enum values."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FrugalityScoreMirror:
    """Mirror of FrugalityScore dataclass."""
    def __init__(self, score: float, level: str, factors: list[dict[str, Any]]) -> None:
        self.score = score
        self.level = level
        self.factors = factors


def _classify_usage_mirror(total_power: float) -> str:
    """Mirror of _classify_usage logic."""
    if total_power < _POWER_THRESHOLD_LOW:
        return EnergyUsageLevelMirror.LOW
    elif total_power < _POWER_THRESHOLD_MODERATE:
        return EnergyUsageLevelMirror.MODERATE
    elif total_power < _POWER_THRESHOLD_HIGH:
        return EnergyUsageLevelMirror.HIGH
    return EnergyUsageLevelMirror.VERY_HIGH


def _calculate_frugality_mirror(
    total_power: float,
    lights_on: int,
    switches_on: int,
) -> FrugalityScoreMirror:
    """Mirror of _calculate_frugality logic."""
    power_score: float = max(0.0, 1.0 - (total_power / _POWER_MAX_NORMAL))
    device_count: int = lights_on + switches_on
    device_score: float = max(0.0, 1.0 - (device_count / 20.0))
    combined_score: float = (power_score * 0.7) + (device_score * 0.3)
    usage_level: str = _classify_usage_mirror(total_power)
    factors: list[dict[str, Any]] = [
        {
            "entity": "sensor.energy_proxy",
            "weight": 0.7,
            "reason": f"power_consumption_{total_power:.0f}w",
            "value": total_power,
        },
        {
            "entity": "sensor.energy_proxy",
            "weight": 0.3,
            "reason": f"active_devices_{device_count}",
            "value": device_count,
        },
    ]
    return FrugalityScoreMirror(
        score=round(combined_score, 2),
        level=usage_level,
        factors=factors,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test Helpers
# ─────────────────────────────────────────────────────────────────────────────

class MockState:
    """Mock State-like object for hass.states.async_all() simulation."""
    def __init__(
        self,
        entity_id: str,
        state: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class MockStates:
    """Mock hass.states namespace."""
    def __init__(self, states: list[MockState]) -> None:
        self._states = states
    
    def async_all(self, domain: str | None = None) -> list[MockState]:
        """Return all states or filtered by domain."""
        if domain is None:
            return self._states
        return [s for s in self._states if s.entity_id.startswith(f"{domain}.")]


class MockHass:
    """Mock HomeAssistant with state categorization."""
    def __init__(self, states: list[MockState]) -> None:
        self.states = MockStates(states)


class MockCoordinator:
    """Mock coordinator for EnergyProxySensor."""
    def __init__(self) -> None:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Tests: native_value (threshold classification)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("power_states", "expected_level"),
    [
        # EP1: low (<100W)
        (
            [
                MockState("sensor.light_power", "50", {"device_class": "power"}),
                MockState("sensor.socket_power", "30", {"device_class": "power"}),
            ],
            EnergyUsageLevelMirror.LOW,
        ),
        # EP2: moderate (100W-499W)
        (
            [
                MockState("sensor.light_power", "150", {"device_class": "power"}),
                MockState("sensor.socket_power", "200", {"device_class": "power"}),
            ],
            EnergyUsageLevelMirror.MODERATE,
        ),
        # EP3: high (500W-1499W)
        (
            [
                MockState("sensor.light_power", "600", {"device_class": "power"}),
                MockState("sensor.socket_power", "700", {"device_class": "power"}),
            ],
            EnergyUsageLevelMirror.HIGH,
        ),
        # EP4: very_high (>=1500W)
        (
            [
                MockState("sensor.light_power", "800", {"device_class": "power"}),
                MockState("sensor.socket_power", "900", {"device_class": "power"}),
            ],
            EnergyUsageLevelMirror.VERY_HIGH,
        ),
        # EP5: zero power → low
        (
            [],
            EnergyUsageLevelMirror.LOW,
        ),
        # EP6: boundary at 100W (exactly threshold → moderate)
        (
            [MockState("sensor.light_power", "100", {"device_class": "power"})],
            EnergyUsageLevelMirror.MODERATE,
        ),
        # EP7: boundary at 500W (exactly threshold → high)
        (
            [MockState("sensor.light_power", "500", {"device_class": "power"})],
            EnergyUsageLevelMirror.HIGH,
        ),
    ],
)
def test_native_value_threshold_classification(
    power_states: list[MockState],
    expected_level: str,
) -> None:
    """EP1-EP7: native_value follows threshold classification."""
    # Build full state list including lights/switches
    all_states: list[MockState] = power_states + [
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    assert sensor._attr_native_value == expected_level


# ─────────────────────────────────────────────────────────────────────────────
# Tests: extra_state_attributes
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("power_states", "lights_on", "switches_on", "expected_total", "expected_count"),
    [
        # EA1: full attributes
        (
            [
                MockState("sensor.light_power", "150.5", {"device_class": "power"}),
                MockState("sensor.socket_power", "250.3", {"device_class": "power"}),
            ],
            3,
            2,
            400.8,
            2,
        ),
        # EA2: defaults (zero power, no devices)
        (
            [],
            0,
            0,
            0.0,
            0,
        ),
        # EA3: partial (only lights on)
        (
            [MockState("sensor.light_power", "75", {"device_class": "power"})],
            5,
            0,
            75.0,
            1,
        ),
    ],
)
def test_extra_state_attributes(
    power_states: list[MockState],
    lights_on: int,
    switches_on: int,
    expected_total: float,
    expected_count: int,
) -> None:
    """EA1-EA3: attrs contain total_power_w, lights_on, switches_on, frugality."""
    all_states: list[MockState] = (
        power_states
        + [MockState(f"light.light{i}", "on") for i in range(lights_on)]
        + [MockState(f"light.light{i}", "off") for i in range(lights_on, 10)]
        + [MockState(f"switch.switch{i}", "on") for i in range(switches_on)]
        + [MockState(f"switch.switch{i}", "off") for i in range(switches_on, 10)]
    )
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    attrs = sensor._attr_extra_state_attributes
    assert attrs is not None
    assert abs(attrs["total_power_w"] - expected_total) < 0.1
    assert attrs["lights_on"] == lights_on
    assert attrs["switches_on"] == switches_on
    assert attrs["power_entities_count"] == expected_count
    assert "frugality_score" in attrs
    assert "usage_level" in attrs


# ─────────────────────────────────────────────────────────────────────────────
# Tests: frugality score calculation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("total_power", "lights_on", "switches_on", "expected_score_range"),
    [
        # FS1: high frugality (low consumption, few devices)
        (0, 0, 0, (0.9, 1.0)),
        # FS2: moderate frugality (moderate consumption)
        (500, 5, 3, (0.5, 0.7)),
        # FS3: low frugality (high consumption, many devices)
        (2000, 15, 10, (0.0, 0.2)),
    ],
)
def test_frugality_score_calculation(
    total_power: float,
    lights_on: int,
    switches_on: int,
    expected_score_range: tuple[float, float],
) -> None:
    """FS1-FS3: frugality score is inverse of consumption."""
    # Create power sensor with exact value
    power_states = [MockState("sensor.main_power", str(total_power), {"device_class": "power"})] if total_power > 0 else []
    all_states: list[MockState] = (
        power_states
        + [MockState(f"light.light{i}", "on") for i in range(lights_on)]
        + [MockState(f"light.light{i}", "off") for i in range(lights_on, 20)]
        + [MockState(f"switch.switch{i}", "on") for i in range(switches_on)]
        + [MockState(f"switch.switch{i}", "off") for i in range(switches_on, 20)]
    )
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    attrs = sensor._attr_extra_state_attributes
    assert attrs is not None
    frugality = attrs["frugality_score"]
    assert expected_score_range[0] <= frugality <= expected_score_range[1]


# ─────────────────────────────────────────────────────────────────────────────
# Tests: edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_edge_unavailable_power_sensor() -> None:
    """EC1: unavailable power sensors are skipped."""
    all_states: list[MockState] = [
        MockState("sensor.main_power", "unavailable", {"device_class": "power"}),
        MockState("sensor.backup_power", "unknown", {"device_class": "power"}),
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    assert sensor._attr_native_value == EnergyUsageLevelMirror.LOW
    assert sensor._attr_extra_state_attributes["total_power_w"] == 0.0


def test_edge_invalid_power_value() -> None:
    """EC2: invalid power values (non-numeric) are skipped."""
    all_states: list[MockState] = [
        MockState("sensor.main_power", "invalid", {"device_class": "power"}),
        MockState("sensor.backup_power", "NaN", {"device_class": "power"}),
        MockState("sensor.good_power", "100", {"device_class": "power"}),
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    assert sensor._attr_native_value == EnergyUsageLevelMirror.MODERATE
    assert sensor._attr_extra_state_attributes["total_power_w"] == 100.0
    assert sensor._attr_extra_state_attributes["power_entities_count"] == 1


def test_edge_negative_power() -> None:
    """EC3: negative power values are skipped (solar feed-in)."""
    all_states: list[MockState] = [
        MockState("sensor.solar_feed", "-500", {"device_class": "power"}),
        MockState("sensor.consumption", "200", {"device_class": "power"}),
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    # 200W is in moderate range (100-499W)
    assert sensor._attr_native_value == EnergyUsageLevelMirror.MODERATE
    assert sensor._attr_extra_state_attributes["total_power_w"] == 200.0


def test_edge_power_entities_capped() -> None:
    """EC4: power_entities list is capped to 10 entries."""
    power_states = [
        MockState(f"sensor.power{i}", str(10 + i), {"device_class": "power"})
        for i in range(15)
    ]
    all_states: list[MockState] = power_states + [
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    attrs = sensor._attr_extra_state_attributes
    assert attrs is not None
    assert len(attrs["power_entities"]) == 10
    assert attrs["power_entities_count"] == 15


def test_edge_extreme_high_power() -> None:
    """EC5: extreme power (>2000W) results in zero power_score floor."""
    all_states: list[MockState] = [
        MockState("sensor.main_power", "3000", {"device_class": "power"}),
        MockState("light.living_room", "off"),
        MockState("switch.tv", "off"),
    ]
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    assert sensor._attr_native_value == EnergyUsageLevelMirror.VERY_HIGH
    attrs = sensor._attr_extra_state_attributes
    # power_score = 0 (3000W > 2000W max), device_score = 1.0 (0 devices)
    # combined = 0*0.7 + 1.0*0.3 = 0.3
    assert attrs["frugality_score"] == 0.3


def test_edge_many_devices_penalty() -> None:
    """EC6: many active devices reduce frugality score."""
    all_states: list[MockState] = (
        [MockState("sensor.main_power", "100", {"device_class": "power"})]
        + [MockState(f"light.light{i}", "on") for i in range(18)]
        + [MockState(f"switch.switch{i}", "on") for i in range(2)]
    )
    hass = MockHass(all_states)
    coordinator = MockCoordinator()
    
    sensor = EnergyProxySensor(coordinator, hass)  # type: ignore[arg-type]
    sensor._update_energy_data()
    
    attrs = sensor._attr_extra_state_attributes
    assert attrs["lights_on"] == 18
    assert attrs["switches_on"] == 2
    # 20 devices = device_score = 0.0, power_score ~0.93 → combined ~0.65
    assert 0.60 <= attrs["frugality_score"] <= 0.70


# ─────────────────────────────────────────────────────────────────────────────
# Global Contract Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_gc1_no_core_api_dependency() -> None:
    """GC1: EnergyProxySensor uses only hass.states.async_all() — no Core API."""
    import inspect
    from custom_components.pilotsuite.sensors.energy_sensors import EnergyProxySensor
    
    source = inspect.getsource(EnergyProxySensor)
    
    # Must NOT contain Core API endpoints
    assert "/api/v1/" not in source
    assert "_core_base_url" not in source
    assert "_fetch(" not in source
    
    # Must use hass.states.async_all
    assert "hass.states.async_all" in source or "self._hass.states.async_all" in source


def test_gc2_no_local_semantic_invention() -> None:
    """GC2: No local ML/heuristics — only threshold logic + aggregation."""
    import inspect
    from custom_components.pilotsuite.sensors.energy_sensors import EnergyProxySensor
    
    source = inspect.getsource(EnergyProxySensor)
    
    # Threshold logic is trivial (if/elif comparisons on total_power)
    assert "if total_power <" in source or "_POWER_THRESHOLD" in source
    assert "elif total_power <" in source or "_POWER_THRESHOLD" in source
    
    # Frugality is simple weighted average
    assert "power_score" in source
    assert "device_score" in source
    
    # No ML, no external calls, no complex heuristics
    assert "model" not in source.lower()
    assert "predict" not in source.lower()
    assert "neural" not in source.lower()
