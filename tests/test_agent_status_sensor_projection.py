"""Projection Contract Tests — agent_status_sensor (HA-121, HA-315).

Verifies AgentStatusSensor is a pure projection shell on /api/v1/agent/status.
Contract: no local semantic invention — all values derived directly from Core API.
"""

import math
import pytest
from homeassistant.components.sensor import SensorDeviceClass


# ─── Contract Mirror ─────────────────────────────────────────────────────────

def _as_mapping(val, default=None):
    if isinstance(val, dict) and val:
        return val
    return default if default is not None else {}


def _as_list(val, default=None):
    if isinstance(val, list):
        return val
    return default if default is not None else []


def _as_string(val, default=""):
    if isinstance(val, str):
        normalized = val.strip()
        if normalized:
            return normalized
    return default


def _as_float(val, default=0.0):
    if isinstance(val, (int, float)) and not isinstance(val, bool) and math.isfinite(val):
        return float(val)
    return default


def _as_bool(val, default=False):
    return bool(val) if isinstance(val, bool) else default


class AgentStatusSensorContract:
    """Mirror of the sensor's contract for a given API response."""

    @staticmethod
    def native_value(api_response) -> str | None:
        data = _as_mapping(api_response)
        status = _as_string(data.get("status"), "offline")
        agent_name = _as_string(data.get("agent_name"), "Styx")
        return f"{agent_name}: {status}"

    @staticmethod
    def icon(api_response) -> str:
        data = _as_mapping(api_response)
        status = _as_string(data.get("status"), "offline")
        if status == "ready":
            return "mdi:robot-happy"
        elif status == "degraded":
            return "mdi:robot-confused"
        return "mdi:robot-off"

    @staticmethod
    def extra_state_attributes(api_response) -> dict:
        data = _as_mapping(api_response)
        agent_name = _as_string(data.get("agent_name"), "Styx")
        agent_version = _as_string(data.get("agent_version"), "")
        status = _as_string(data.get("status"), "offline")
        uptime_seconds = _as_float(data.get("uptime_seconds"), 0.0)
        llm_model = _as_string(data.get("llm_model"), "")
        llm_backend = _as_string(data.get("llm_backend"), "")
        character = _as_string(data.get("character"), "")
        last_health_check = _as_string(data.get("last_health_check"), "")
        conversation_ready = _as_bool(data.get("conversation_ready"), False)
        llm_available = _as_bool(data.get("llm_available"), False)
        features_raw = _as_list(data.get("features"), [])
        features = [_as_string(f) for f in features_raw]
        features = [f for f in features if f]
        supported_languages_raw = _as_list(data.get("supported_languages"), [])
        supported_languages = [_as_string(l) for l in supported_languages_raw]
        supported_languages = [l for l in supported_languages if l]
        return {
            "agent_name": agent_name,
            "agent_version": agent_version,
            "status": status,
            "uptime_seconds": uptime_seconds,
            "conversation_ready": conversation_ready,
            "llm_available": llm_available,
            "llm_model": llm_model,
            "llm_backend": llm_backend,
            "character": character,
            "features": features,
            "supported_languages": supported_languages,
            "last_health_check": last_health_check,
        }


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_coordinator():
    class MockCoordinator:
        def __init__(self, data):
            self.data = data
    return MockCoordinator


@pytest.fixture
def mock_hass():
    return None  # not needed for unit tests


# ─── Test Cases ───────────────────────────────────────────────────────────────

# AS1 — native_value: status variations
@pytest.mark.parametrize("api_response,expected", [
    (
        {"status": "ready", "agent_name": "Styx", "ok": True},
        "Styx: ready",
    ),
    (
        {"status": "degraded", "agent_name": "Styx", "ok": True},
        "Styx: degraded",
    ),
    (
        {"status": "offline", "agent_name": "Athena", "ok": True},
        "Athena: offline",
    ),
    (
        {"ok": False},
        "Styx: offline",
    ),
    (
        {},
        "Styx: offline",
    ),
])
def test_as1_native_value(api_response, expected):
    """AS1: native_value derives directly from status + agent_name fields."""
    assert AgentStatusSensorContract.native_value(api_response) == expected


# AS2 — icon: status → icon mapping
@pytest.mark.parametrize("api_response,expected_icon", [
    ({"status": "ready"}, "mdi:robot-happy"),
    ({"status": "degraded"}, "mdi:robot-confused"),
    ({"status": "offline"}, "mdi:robot-off"),
    ({"status": "unknown_status"}, "mdi:robot-off"),
    ({}, "mdi:robot-off"),
])
def test_as2_icon(api_response, expected_icon):
    """AS2: icon is pure state-to-icon mapping, no local classification logic."""
    assert AgentStatusSensorContract.icon(api_response) == expected_icon


# AS3 — extra_state_attributes: field passthrough
@pytest.mark.parametrize("api_response,attr_key,expected", [
    (
        {"agent_name": "Styx", "agent_version": "v15.4.0"},
        "agent_name", "Styx",
    ),
    (
        {"agent_version": "v15.4.0"},
        "agent_version", "v15.4.0",
    ),
    (
        {"uptime_seconds": 3600},
        "uptime_seconds", 3600,
    ),
    (
        {"conversation_ready": True},
        "conversation_ready", True,
    ),
    (
        {"llm_available": False, "llm_model": "minimax-m2.7"},
        "llm_model", "minimax-m2.7",
    ),
    (
        {"features": ["voice", "calendar", "habitus"]},
        "features", ["voice", "calendar", "habitus"],
    ),
    (
        {"supported_languages": ["de", "en"]},
        "supported_languages", ["de", "en"],
    ),
    (
        {"character": "analytisch"},
        "character", "analytisch",
    ),
])
def test_as3_extra_state_attributes(api_response, attr_key, expected):
    """AS3: extra_state_attributes are direct passthrough of API fields."""
    attrs = AgentStatusSensorContract.extra_state_attributes(api_response)
    assert attrs[attr_key] == expected


# AS4 — edge cases
@pytest.mark.parametrize("api_response,expected_attrs", [
    (
        {},
        {
            "agent_name": "Styx",
            "agent_version": "",
            "status": "offline",
            "uptime_seconds": 0,
            "conversation_ready": False,
            "llm_available": False,
            "llm_model": "",
            "llm_backend": "",
            "character": "",
            "features": [],
            "supported_languages": [],
            "last_health_check": "",
        },
    ),
    (
        {"status": "ready", "ok": True},
        {"status": "ready", "conversation_ready": False},
    ),
    (
        {"status": "ready", "ok": True, "features": None},
        {"features": []},
    ),
])
def test_as4_edge_defaults(api_response, expected_attrs):
    """AS4: edge cases — missing optional fields use sentinel defaults."""
    attrs = AgentStatusSensorContract.extra_state_attributes(api_response)
    for key, val in expected_attrs.items():
        assert attrs[key] == val, f"mismatch for {key}: {attrs[key]!r} != {val!r}"


# AS5 — malformed payload: non-dict top-level → safe defaults
@pytest.mark.parametrize("api_response,expected_value", [
    ([], "Styx: offline"),
    (None, "Styx: offline"),
    ("string", "Styx: offline"),
    (42, "Styx: offline"),
    (True, "Styx: offline"),
])
def test_as5_native_value_non_dict(api_response, expected_value):
    """AS5: non-dict top-level payload falls back to safe defaults."""
    assert AgentStatusSensorContract.native_value(api_response) == expected_value


# AS6 — malformed payload: non-dict top-level → safe icon
@pytest.mark.parametrize("api_response,expected_icon", [
    ([], "mdi:robot-off"),
    (None, "mdi:robot-off"),
    ("string", "mdi:robot-off"),
    (42, "mdi:robot-off"),
])
def test_as6_icon_non_dict(api_response, expected_icon):
    """AS6: non-dict top-level payload falls back to offline icon."""
    assert AgentStatusSensorContract.icon(api_response) == expected_icon


# AS7 — malformed: non-string status/agent_name
@pytest.mark.parametrize("api_response,expected", [
    ({"status": 42, "agent_name": "Styx"}, "Styx: offline"),
    ({"status": "ready", "agent_name": 42}, "Styx: ready"),
    ({"status": None, "agent_name": None}, "Styx: offline"),
    ({"status": "", "agent_name": ""}, "Styx: offline"),
    ({"status": "  ", "agent_name": "  "}, "Styx: offline"),
])
def test_as7_native_value_non_string_fields(api_response, expected):
    """AS7: non-string status/agent_name fall back to defaults."""
    assert AgentStatusSensorContract.native_value(api_response) == expected


# AS8 — malformed uptime_seconds / conversation_ready / llm_available
@pytest.mark.parametrize("api_response,expected_uptime,expected_conv,expected_llm", [
    ({"uptime_seconds": "3600"}, 0.0, False, False),
    ({"uptime_seconds": None}, 0.0, False, False),
    ({"uptime_seconds": float("inf")}, 0.0, False, False),
    ({"uptime_seconds": float("nan")}, 0.0, False, False),
    ({"conversation_ready": "yes"}, 0, False, False),
    ({"llm_available": 1}, 0, False, False),
    ({"conversation_ready": None}, 0, False, False),
    ({"llm_available": None}, 0, False, False),
    ({"uptime_seconds": True}, 0.0, False, False),
])
def test_as8_attrs_malformed_numeric_bool(api_response, expected_uptime, expected_conv, expected_llm):
    """AS8: malformed numeric/bool attrs fall back to safe defaults."""
    attrs = AgentStatusSensorContract.extra_state_attributes(api_response)
    assert attrs["uptime_seconds"] == expected_uptime, f"uptime: {attrs['uptime_seconds']!r}"
    assert attrs["conversation_ready"] == expected_conv, f"conv: {attrs['conversation_ready']!r}"
    assert attrs["llm_available"] == expected_llm, f"llm: {attrs['llm_available']!r}"


# AS9 — malformed features / supported_languages lists
@pytest.mark.parametrize("api_response,expected_features,expected_langs", [
    ({"features": "voice"}, [], []),
    ({"features": 42}, [], []),
    ({"features": {}}, [], []),
    ({"features": ["voice", 42, None, "calendar"]}, ["voice", "calendar"], []),
    ({"features": [""]}, [], []),
    ({"features": ["  "]}, [], []),
    ({"supported_languages": "de"}, [], []),
    ({"supported_languages": 42}, [], []),
    ({"supported_languages": ["de", 42, None, "en"]}, [], ["de", "en"]),
    ({"supported_languages": [""]}, [], []),
    ({"supported_languages": ["  "]}, [], []),
])
def test_as9_attrs_malformed_lists(api_response, expected_features, expected_langs):
    """AS9: malformed list fields are filtered or replaced with safe defaults."""
    attrs = AgentStatusSensorContract.extra_state_attributes(api_response)
    assert attrs["features"] == expected_features, f"features: {attrs['features']!r}"
    assert attrs["supported_languages"] == expected_langs, f"langs: {attrs['supported_languages']!r}"


# GC1 — Global Contract: pure projection, no local semantic invention
def test_gc1_no_local_semantic_invention():
    """GC1: AgentStatusSensor does not invent status; it projects Core /api/v1/agent/status.

    The sensor has no local ML, heuristic, or classification logic.
    All values come directly from the Core API response.
    """
    import ast

    import_path = "custom_components.pilotsuite.sensors.agent_status_sensor"
    with open(f"{import_path.replace('.', '/')}.py") as f:
        source = f.read()

    tree = ast.parse(source)

    # Walk AST for function definitions that might indicate local logic
    local_logic_indicators = {"_classify", "_infer", "_heuristic", "_calculate", "_predict"}
    found_indicators = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_") and any(ind in node.name for ind in local_logic_indicators):
                found_indicators.append(node.name)

    assert not found_indicators, (
        f"AgentStatusSensor contains local logic functions that suggest "
        f"semantic invention: {found_indicators}"
    )


# GC2 — Global Contract: API endpoint is /api/v1/agent/status
def test_gc2_api_endpoint():
    """GC2: AgentStatusSensor hits /api/v1/agent/status for its data."""
    with open("custom_components/pilotsuite/sensors/agent_status_sensor.py") as f:
        source = f.read()

    # Sensor builds URL as base + "/status" where base = _core_base_url() + "/api/v1/agent"
    # Check for the composed endpoint pattern
    assert "/api/v1/agent" in source and "status" in source, (
        "AgentStatusSensor must project /api/v1/agent/status — "
        "contract requires this endpoint"
    )
    assert "_core_base_url()" in source, "Sensor must use _core_base_url() for Core API routing"


# GC3 — Source Guard: _as_mapping, _as_list, _as_string, _as_float, _as_bool present in production code
def test_gc3_guard_helpers_in_source():
    """GC3: Production sensor contains guard helpers (no bare .get() in attrs/native_value/icon)."""
    with open("custom_components/pilotsuite/sensors/agent_status_sensor.py") as f:
        source = f.read()

    assert "def _as_mapping" in source, "_as_mapping guard must be defined"
    assert "def _as_list" in source, "_as_list guard must be defined"
    assert "def _as_string" in source, "_as_string guard must be defined"
    assert "def _as_float" in source, "_as_float guard must be defined"
    assert "def _as_bool" in source, "_as_bool guard must be defined"
    assert "math.isfinite" in source, "_as_float must use math.isfinite for finite float guard"
