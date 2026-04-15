"""Projection contract for performance_scaling.py entity_id prefix parity.

HA-472: Ensure performance_scaling.py uses canonical pilotsuite entity_id
prefixes, not hardcoded stale copilot_ha strings.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "core" / "modules" / "performance_scaling.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestPerformanceScalingProjection:
    """Entity-id prefix contract for performance_scaling.py."""

    def test_ps1_count_entities_uses_pilotsuite_prefixes(self) -> None:
        """PS1: _count_entities uses pilotsuite entity_id prefixes."""
        source = _read_source()
        # _count_entities must use sensor.pilotsuite, button.pilotsuite,
        # binary_sensor.pilotsuite — not copilot_ha variants
        assert 'entity_id.startswith("sensor.pilotsuite")' in source, (
            "_count_entities must count sensor.pilotsuite entities"
        )
        assert 'entity_id.startswith("button.pilotsuite")' in source, (
            "_count_entities must count button.pilotsuite entities"
        )
        assert 'entity_id.startswith("binary_sensor.pilotsuite")' in source, (
            "_count_entities must count binary_sensor.pilotsuite entities"
        )

    def test_ps2_no_stale_copilot_ha_entity_id_prefixes(self) -> None:
        """PS2: AST scan — zero unexplained copilot_ha entity_id prefixes."""
        source = _read_source()
        tree = ast.parse(source)

        stale_prefixes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if isinstance(arg, (ast.Constant, ast.Str)):
                        val = arg.value if isinstance(arg, ast.Constant) else arg.value
                        if isinstance(val, str) and "copilot_ha" in val:
                            stale_prefixes.append(
                                f"startswith({val!r}) at line {node.lineno}"
                            )
                for kw in node.keywords:
                    if kw.arg == "prefix" or kw.arg == "entity_id":
                        if isinstance(kw.value, (ast.Constant, ast.Str)):
                            val = kw.value.value if isinstance(kw.value, ast.Constant) else kw.value.value
                            if isinstance(val, str) and "copilot_ha" in val:
                                stale_prefixes.append(
                                    f"{kw.arg}=startswith({val!r}) at line {node.lineno}"
                                )

        assert stale_prefixes == [], (
            f"Found stale copilot_ha entity_id prefixes: {stale_prefixes}"
        )

    def test_ps3_syntax_ok(self) -> None:
        """PS3: module compiles without syntax errors."""
        source = _read_source()
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in performance_scaling.py: {e}")
