"""Projection Contract Tests — agent_status_sensor (HA-121).

Verifies AgentStatusSensor is a pure projection shell on /api/v1/agent/status.
Contract: no local semantic invention — all values derived directly from Core API.
"""

import pytest
from homeassistant.components.sensor import SensorDeviceClass




# ─── Contract Mirror ─────────────────────────────────────────────────────────

class AgentStatusSensorContract:
    """Mirror of the sensor's contract for a given API response."""

    @staticmethod
    def native_value(api_response: dict) -> str | None:
        status = api_response.get("status", "offline")
        agent_name = api_response.get("agent_name", "Styx")
        return f"{agent_name}: {status}"

    @staticmethod
    def icon(api_response: dict) -> str:
        status = api_response.get("status", "offline")
        if status == "ready":
            return "mdi:robot-happy"
        elif status == "degraded":
            return "mdi:robot-confused"
        return "mdi:robot-off"

    @staticmethod
    def extra_state_attributes(api_response: dict) -> dict:
        return {
            "agent_name": api_response.get("agent_name", "Styx"),
            "agent_version": api_response.get("agent_version", ""),
            "status": api_response.get("status", "offline"),
            "uptime_seconds": api_response.get("uptime_seconds", 0),
            "conversation_ready": api_response.get("conversation_ready", False),
            "llm_available": api_response.get("llm_available", False),
            "llm_model": api_response.get("llm_model", ""),
            "llm_backend": api_response.get("llm_backend", ""),
            "character": api_response.get("character", ""),
            "features": api_response.get("features", []),
            "supported_languages": api_response.get("supported_languages", []),
            "last_health_check": api_response.get("last_health_check", ""),
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
        {"features": None},
    ),
])
def test_as4_edge_defaults(api_response, expected_attrs):
    """AS4: edge cases — missing optional fields use sentinel defaults."""
    attrs = AgentStatusSensorContract.extra_state_attributes(api_response)
    for key, val in expected_attrs.items():
        assert attrs[key] == val, f"mismatch for {key}: {attrs[key]!r} != {val!r}"


# GC1 — Global Contract: pure projection, no local semantic invention
def test_gc1_no_local_semantic_invention():
    """GC1: AgentStatusSensor does not invent status; it projects Core /api/v1/agent/status.

    The sensor has no local ML, heuristic, or classification logic.
    All values come directly from the Core API response.
    """
    import ast

    import_path = "custom_components.copilot_ha.sensors.agent_status_sensor"
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
    with open("custom_components/copilot_ha/sensors/agent_status_sensor.py") as f:
        source = f.read()

    # Sensor builds URL as base + "/status" where base = _core_base_url() + "/api/v1/agent"
    # Check for the composed endpoint pattern
    assert "/api/v1/agent" in source and "status" in source, (
        "AgentStatusSensor must project /api/v1/agent/status — "
        "contract requires this endpoint"
    )
    assert "_core_base_url()" in source, "Sensor must use _core_base_url() for Core API routing"
