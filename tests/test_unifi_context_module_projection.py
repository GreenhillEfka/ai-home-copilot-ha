"""Projection contract for unifi_context_module.py hass.data parity.

HA-470: Ensure unifi_context_module.py uses canonical hass.data["pilotsuite"]
lookup, not a hardcoded stale copilot_ha string.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "core" / "modules" / "unifi_context_module.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestUnifiContextModuleProjection:
    """hass.data reference contract for unifi_context_module.py."""

    def test_ucm1_get_network_module_uses_pilotsuite(self) -> None:
        """UCM1: get_network_module uses pilotsuite, not copilot_ha."""
        source = _read_source()
        # get_network_module is a module-level function
        assert "def get_network_module" in source
        # Must use pilotsuite in the hass.data.get call
        assert 'hass.data.get("pilotsuite"' in source, (
            "get_network_module must use hass.data.get('pilotsuite', ...)"
        )

    def test_ucm2_no_stale_copilot_ha_hass_data_refs(self) -> None:
        """UCM2: AST scan — zero unexplained copilot_ha hass.data refs."""
        source = _read_source()
        tree = ast.parse(source)

        stale_hass_data_refs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                val = node.value
                # hass.data["copilot_ha"] or hass.data.get("copilot_ha")
                if isinstance(val, ast.Attribute):
                    if val.attr == "data":
                        if isinstance(node.slice, (ast.Constant, ast.Str)):
                            key = node.slice.value if isinstance(node.slice, ast.Constant) else node.slice.value
                            if key == "copilot_ha":
                                stale_hass_data_refs.append(f"hass.data['copilot_ha'] at line {node.lineno}")

        assert stale_hass_data_refs == [], (
            f"Found stale copilot_ha hass.data refs: {stale_hass_data_refs}"
        )

    def test_ucm3_syntax_ok(self) -> None:
        """UCM3: module parses without syntax errors."""
        source = _read_source()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in unifi_context_module.py: {e}")
