"""Projection contract for knowledge_graph_sync.py hass.data parity.

HA-471: Ensure knowledge_graph_sync.py uses canonical hass.data["pilotsuite"]
lookup, not hardcoded stale copilot_ha strings.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "core" / "modules" / "knowledge_graph_sync.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestKnowledgeGraphSyncProjection:
    """hass.data reference contract for knowledge_graph_sync.py."""

    def test_kg1_async_setup_uses_pilotsuite(self) -> None:
        """KG1: async_setup passes use pilotsuite, not copilot_ha."""
        source = _read_source()
        # async_setup is the module class __init__ — check the hass.data.get call
        assert 'hass.data.get("pilotsuite"' in source, (
            "async_setup must use hass.data.get('pilotsuite', {}) for runtime lookup"
        )

    def test_kg2_no_stale_copilot_ha_hass_data_refs(self) -> None:
        """KG2: AST scan — zero unexplained copilot_ha hass.data refs."""
        source = _read_source()
        tree = ast.parse(source)

        stale_hass_data_refs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                val = node.value
                if isinstance(val, ast.Attribute) and val.attr == "data":
                    if isinstance(node.slice, (ast.Constant, ast.Str)):
                        key = node.slice.value if isinstance(node.slice, ast.Constant) else node.slice.value
                        if key == "copilot_ha":
                            stale_hass_data_refs.append(f"hass.data['copilot_ha'] at line {node.lineno}")

        assert stale_hass_data_refs == [], (
            f"Found stale copilot_ha hass.data refs: {stale_hass_data_refs}"
        )

    def test_kg3_async_get_uses_pilotsuite(self) -> None:
        """KG3: async_get_knowledge_graph_sync uses pilotsuite, not copilot_ha."""
        source = _read_source()
        assert 'hass.data.get("pilotsuite"' in source, (
            "async_get_knowledge_graph_sync must use hass.data.get('pilotsuite', {}) for runtime lookup"
        )

    def test_kg4_syntax_ok(self) -> None:
        """KG4: module parses without syntax errors."""
        source = _read_source()
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"knowledge_graph_sync.py has a syntax error: {exc}")