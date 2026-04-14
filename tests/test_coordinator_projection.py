"""Projection contract for coordinator.py ML context hass.data parity.

HA-467: Ensure coordinator.py uses canonical hass.data["pilotsuite"]
lookup, not a hardcoded stale copilot_ha string.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "coordinator.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestCoordinatorProjection:
    """ML context hass.data reference contract for coordinator.py."""

    def test_cd1_no_stale_copilot_ha_in_get_habit_learning_data(self) -> None:
        """CD1: _get_habit_learning_data uses pilotsuite, not copilot_ha."""
        source = _read_source()
        # Isolate the _get_habit_learning_data method body
        m = re.search(
            r'async def _get_habit_learning_data\(self\).*?(?=\n    async def |\n    def |\Z)',
            source,
            re.DOTALL,
        )
        assert m, "_get_habit_learning_data method not found"
        method_body = m.group(0)
        # Must use pilotsuite, not copilot_ha
        assert "pilotsuite" in method_body, (
            "_get_habit_learning_data must use 'pilotsuite' as the hass.data key"
        )
        assert "copilot_ha" not in method_body, (
            "_get_habit_learning_data must not contain hardcoded 'copilot_ha'; "
            "use 'pilotsuite' instead"
        )

    def test_cd2_ast_scan_no_unexplained_copilot_ha_literal(self) -> None:
        """CD2: AST scan — no unexplained copilot_ha literals in coordinator.py."""
        source = _read_source()
        # These patterns are LEGITIMATE legacy-bridge migration comments, not production refs
        LEGITIMATE = re.compile(r'LEGACY_DOMAIN|llegacy.*copilot_ha|legacy.*mirror|copilot_ha/')
        for lineno, line in enumerate(source.splitlines(), 1):
            if "copilot_ha" in line:
                assert LEGITIMATE.search(line), (
                    f"Line {lineno} contains unexplained copilot_ha literal: {line.strip()}"
                )

    def test_cd3_syntax_ok(self) -> None:
        """CD3: coordinator.py is syntactically valid."""
        source = _read_source()
        try:
            ast.parse(source, filename=str(TARGET_FILE))
        except SyntaxError as e:
            pytest.fail(f"coordinator.py has a SyntaxError: {e}")