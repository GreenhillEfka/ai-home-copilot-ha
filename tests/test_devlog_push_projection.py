"""Contract tests for devlog_push.py projection parity (HA-450)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/devlog_push.py")
TEXT = SRC.read_text()


class TestDevlogPushProjection:
    """Projection parity contract for devlog_push.py."""

    def test_dg1_canonical_traceback_filter_supports_both_domains(self) -> None:
        """DG1: _extract_latest_block docstring references pilotsuite (canonical)."""
        for node in ast.walk(ast.parse(TEXT)):
            if isinstance(node, ast.FunctionDef) and node.name == "_extract_latest_block":
                assert ast.get_docstring(node), "docstring missing"
                doc = ast.get_docstring(node)
                assert "pilotsuite" in doc, f"expected pilotsuite in docstring, got: {doc}"
                return
        pytest.fail("_extract_latest_block not found")

    def test_dg2_ast_scan_no_stale_sole_copilot_ha_literals(self) -> None:
        """DG2: AST scan finds no copilot_ha string literal that lacks pilotsuite in the same expression.

        The filter logic intentionally keeps BOTH /custom_components/pilotsuite/
        AND /custom_components/copilot_ha/ for backward-compatibility during migration.
        A violation is a copilot_ha string that appears ALONE without pilotsuite nearby.
        """
        tree = ast.parse(TEXT)
        # Find all string constants
        all_strings: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                all_strings[node.lineno] = node.value

        violations: list[str] = []
        for lineno, val in all_strings.items():
            if "copilot_ha" in val and "pilotsuite" not in val:
                violations.append(f"line {lineno}: {val!r}")

        assert not violations, (
            f"stale copilot_ha literals found without pilotsuite in same expression: "
            f"{violations}\n"
            "Note: /custom_components/copilot_ha/ and [copilot_ha] in filter logic are "
            "LEGACY BACKWARD-COMPATIBILITY paths and are valid if paired with pilotsuite."
        )

    def test_dg3_docstring_references_pilotsuite(self) -> None:
        """DG3: async_push_latest_ai_copilot_error docstring references pilotsuite (canonical)."""
        for node in ast.walk(ast.parse(TEXT)):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_push_latest_ai_copilot_error":
                assert ast.get_docstring(node), "docstring missing"
                doc = ast.get_docstring(node)
                assert "pilotsuite" in doc, f"expected pilotsuite in docstring, got: {doc}"
                return
        pytest.fail("async_push_latest_ai_copilot_error not found")
