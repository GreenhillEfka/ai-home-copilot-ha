"""Contract Tests — webhook event domain parity (HA-484).

Verifies that webhook.py fires HA bus events with the pilotsuite-domain
prefix and that card_assets.py serves cards at the pilotsuite URL path.
Both production modules use f"{DOMAIN}_..." where DOMAIN="pilotsuite".

HA-484 — 2026-04-15
"""
from __future__ import annotations

from unittest.mock import MagicMock


class FakeBus:
    def __init__(self):
        self.events = []

    def async_fire(self, event_type, event_data=None):
        self.events.append((event_type, event_data or {}))


class FakeHass:
    def __init__(self):
        self.bus = FakeBus()


def test_webhook_event_names_use_pilotsuite_domain():
    """All f"{DOMAIN}_..." bus fire calls must use pilotsuite, not copilot_ha."""
    # Read the constants directly from webhook.py source to avoid import path issues
    import ast

    src_path = "custom_components/pilotsuite/webhook.py"
    with open(src_path, "r") as f:
        tree = ast.parse(f.read())

    # Find EVENT_TYPE_AUTONOMY_EXECUTED = "autonomy_executed"
    event_constants = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.startswith("EVENT_TYPE_"):
                    if isinstance(node.value, ast.Constant):
                        event_constants[t.id] = node.value.value

    assert "EVENT_TYPE_AUTONOMY_EXECUTED" in event_constants
    assert "EVENT_TYPE_SCENE_CAPTURED" in event_constants

    # Find DOMAIN — can be defined directly or imported from const
    domain = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "DOMAIN":
                    if isinstance(node.value, ast.Constant):
                        domain = node.value.value

    # If DOMAIN is not defined in this file, check const.py
    if domain is None:
        const_path = "custom_components/pilotsuite/const.py"
        with open(const_path, "r") as f:
            const_tree = ast.parse(f.read())
        for node in ast.walk(const_tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "DOMAIN":
                        if isinstance(node.value, ast.Constant):
                            domain = node.value.value

    assert domain == "pilotsuite", f"DOMAIN must be pilotsuite, got {domain}"

    # Verify f-strings that build event names contain DOMAIN
    fstring_domain_usages = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    if isinstance(part.value, ast.Name) and part.value.id == "DOMAIN":
                        fstring_domain_usages.append(node)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "async_fire":
                    for arg in node.args:
                        if isinstance(arg, ast.JoinedStr):
                            for part in arg.values:
                                if isinstance(part, ast.FormattedValue):
                                    if isinstance(part.value, ast.Name) and part.value.id == "DOMAIN":
                                        fstring_domain_usages.append(arg)

    # There should be at least 2 f"{DOMAIN}_..." calls: autonomy_executed + scene_captured
    assert len(fstring_domain_usages) >= 2, (
        f"Expected at least 2 f'{{DOMAIN}}_...' async_fire calls, "
        f"got {len(fstring_domain_usages)}"
    )


def test_webhook_contract_event_expectations_match_production():
    """The production module fires pilotsuite-prefixed events.

    This test documents that any test claiming copilot_ha_ event names
    is stale and must be updated to pilotsuite_ to match the DOMAIN contract.
    """
    import ast

    src_path = "custom_components/pilotsuite/webhook.py"
    with open(src_path, "r") as f:
        src = f.read()
        tree = ast.parse(src)

    # DOMAIN is pilotsuite — fire calls with f"{DOMAIN}_<event>" produce pilotsuite_<event>
    # Verify the two critical events use the DOMAIN variable
    autonomy_calls = []
    scene_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "async_fire":
                for arg in node.args:
                    if isinstance(arg, ast.JoinedStr):
                        src_lines = src.split("\n")
                        lineno = getattr(arg, "lineno", 0)
                        line = src_lines[lineno - 1] if lineno > 0 else ""
                        if "autonomy_executed" in line:
                            autonomy_calls.append(line.strip())
                        if "scene_captured" in line:
                            scene_calls.append(line.strip())

    assert len(autonomy_calls) >= 1, "No pilotsuite autonomy_executed fire call found"
    assert len(scene_calls) >= 1, "No pilotsuite scene_captured fire call found"

    # Confirm the calls use DOMAIN variable (f-string with DOMAIN)
    for call in autonomy_calls + scene_calls:
        assert "DOMAIN" in call, f"Event fire call does not use DOMAIN variable: {call}"


def test_card_assets_url_uses_domain_variable():
    """card_assets.py get_card_asset_url must build URL from DOMAIN variable."""
    import ast

    src_path = "custom_components/pilotsuite/card_assets.py"
    with open(src_path, "r") as f:
        src = f.read()
        tree = ast.parse(src)

    # Find get_card_asset_url function
    found_domain_ref = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_card_asset_url":
            for child in ast.walk(node):
                if isinstance(child, ast.JoinedStr):
                    for part in child.values:
                        if isinstance(part, ast.FormattedValue):
                            if isinstance(part.value, ast.Name) and part.value.id == "DOMAIN":
                                found_domain_ref = True

    assert found_domain_ref, (
        "get_card_asset_url does not use DOMAIN variable in its URL f-string; "
        "it must use f'/api/{DOMAIN}/cards/{{filename}}' to stay in sync with the domain rename"
    )


def test_stale_copilot_ha_webhook_test_contract():
    """Any test asserting 'copilot_ha_autonomy_executed' or 'copilot_ha_scene_captured'
    is stale — the production module fires 'pilotsuite_<event>' per DOMAIN contract."""
    import ast

    test_file = "custom_components/pilotsuite/tests/test_webhook_contract.py"
    with open(test_file, "r") as f:
        src = f.read()

    # Check for stale copilot_ha_ event assertions
    stale_found = []
    for i, line in enumerate(src.split("\n"), 1):
        if '"copilot_ha_autonomy_executed"' in line or '"copilot_ha_scene_captured"' in line:
            stale_found.append((i, line.strip()))

    # After HA-484 edits, these should be gone (assertions now use pilotsuite_)
    assert len(stale_found) == 0, (
        f"Found {len(stale_found)} stale copilot_ha_ event assertions at "
        f"{test_file}: {stale_found} — these must be updated to pilotsuite_ "
        f"to match the production DOMAIN='pilotsuite' contract"
    )


def test_stale_copilot_ha_card_url_contract():
    """Any test asserting '/api/copilot_ha/cards/...' is stale — card_assets.py
    now uses f'/api/{{DOMAIN}}/cards/...' where DOMAIN='pilotsuite'."""
    import ast

    test_file = "custom_components/pilotsuite/tests/test_core_proxy_views.py"
    with open(test_file, "r") as f:
        src = f.read()

    stale_found = []
    for i, line in enumerate(src.split("\n"), 1):
        if '"/api/copilot_ha/cards/' in line:
            stale_found.append((i, line.strip()))

    # After HA-484 edits, this should be gone
    assert len(stale_found) == 0, (
        f"Found stale /api/copilot_ha/cards/ URL assertion at "
        f"{test_file}: {stale_found} — must be updated to /api/pilotsuite/cards/"
    )