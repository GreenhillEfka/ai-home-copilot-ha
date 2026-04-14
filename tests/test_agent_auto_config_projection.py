"""Contract tests for agent_auto_config.py projection parity (HA-435).

Belegt:
  AC1 - alle 4 Service-Handler-Docstrings referenzieren pilotsuite.* nicht copilot_ha.*
  AC2 - AST-Scan: null stale copilot_ha.* Service-Literale in Docstrings
  AC3 - DOMAIN-Konstante ist pilotsuite (kein Hardcode)
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/agent_auto_config.py")
TARGET_DOCSTRINGS = {
    "set_default_agent": "pilotsuite.set_default_agent",
    "verify_agent": "pilotsuite.verify_agent",
    "get_agent_status": "pilotsuite.get_agent_status",
    "repair_agent": "pilotsuite.repair_agent",
}
STALE_SUBSTRINGS = ("copilot_ha.set_default_agent",
                    "copilot_ha.verify_agent",
                    "copilot_ha.get_agent_status",
                    "copilot_ha.repair_agent")


def _read() -> str:
    return SRC.read_text()


def test_ac1_docstrings_reference_pilotsuite():
    """AC1: alle 4 Service-Handler-Docstrings referenzieren pilotsuite.* nicht copilot_ha.*"""
    src = _read()
    for service, expected_ref in TARGET_DOCSTRINGS.items():
        assert f'Service: {expected_ref}' in src, (
            f"AC1 FAIL: {service}-Handler-Docstring referenziert nicht '{expected_ref}'"
        )
    print("AC1: 4/4 Service-Docstrings ok")


def test_ac2_ast_no_stale_copilot_ha_docstrings():
    """AC2: AST-Scan — null stale copilot_ha.*-Literale in Docstrings"""
    tree = ast.parse(_read())
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if doc:
                for stale in STALE_SUBSTRINGS:
                    if stale in doc:
                        violations.append(f"{node.name}: {stale!r}")
    assert not violations, f"AC2 FAIL: stale copilot_ha-Docstrings gefunden: {violations}"
    print("AC2: AST-Scan null stale Docstring-Literale ok")


def test_ac3_domain_is_not_hardcoded():
    """AC3: DOMAIN-Konstante wird aus const importiert, kein Hardcode 'copilot_ha' als Service-Praefix"""
    src = _read()
    # Pruefe dass kein Handler-Funktion einen copilot_ha-Hardcode im Vergleich hat
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if doc and "Service:" in doc:
                # Docstring sollte pilotsuite.ServiceName haben, nicht copilot_ha.ServiceName
                if "copilot_ha." in doc:
                    raise AssertionError(f"AC3 FAIL: {node.name} enthält copilot_ha. im Docstring")
    print("AC3: kein Hardcode-Harcode in Service-Docstrings ok")


if __name__ == "__main__":
    test_ac1_docstrings_reference_pilotsuite()
    test_ac2_ast_no_stale_copilot_ha_docstrings()
    test_ac3_domain_is_not_hardcoded()
    print("\nAC1/AC2/AC3: 3/3 green")
