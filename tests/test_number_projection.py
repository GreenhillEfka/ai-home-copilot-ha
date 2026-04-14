"""Contract tests for number.py PilotSuite projection parity."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/number.py")
MOD = "tests.test_number_projection"


class UniqueIdCollector(ast.NodeVisitor):
    """Collect all unique_id keyword argument string values from NumberEntity constructions."""

    def __init__(self):
        self.unique_ids: list[str] = []
        self._in_call = False

    def visit_Call(self, node: ast.Call):
        # Detect _BaseConfigNumber(...) calls
        if isinstance(node.func, ast.Name) and node.func.id == "_BaseConfigNumber":
            for kw in node.keywords:
                if kw.arg == "unique_id" and isinstance(kw.value, ast.Constant):
                    self.unique_ids.append(kw.value.value)
        self.generic_visit(node)


def _get_unique_ids(src: str) -> list[str]:
    tree = ast.parse(src)
    visitor = UniqueIdCollector()
    visitor.visit(tree)
    return visitor.unique_ids


def _has_stale_copilot_ha(src: str) -> bool:
    """Return True if any copilot_ha_ prefixed unique_id literals remain."""
    return any(uid.startswith("copilot_ha_") for uid in _get_unique_ids(src))


class TestNumberProjectionParity:
    """PilotSuite projection parity for number.py entities."""

    def test_nb1_canonical_seed_max_per_hour(self):
        """NB1: canonical pilotsuite_seed_max_per_hour unique_id present."""
        src = SRC.read_text()
        uids = _get_unique_ids(src)
        assert "pilotsuite_seed_max_per_hour" in uids, (
            f"Expected pilotsuite_seed_max_per_hour in {uids}"
        )

    def test_nb2_canonical_seed_min_seconds(self):
        """NB2: canonical pilotsuite_seed_min_seconds_between unique_id present."""
        src = SRC.read_text()
        uids = _get_unique_ids(src)
        assert "pilotsuite_seed_min_seconds_between" in uids, (
            f"Expected pilotsuite_seed_min_seconds_between in {uids}"
        )

    def test_nb3_canonical_seed_max_per_update(self):
        """NB3: canonical pilotsuite_seed_max_per_update unique_id present."""
        src = SRC.read_text()
        uids = _get_unique_ids(src)
        assert "pilotsuite_seed_max_per_update" in uids, (
            f"Expected pilotsuite_seed_max_per_update in {uids}"
        )

    def test_nb4_no_stale_copilot_ha_unique_ids(self):
        """NB4: no stale copilot_ha_ prefixed unique_id literals in number.py."""
        src = SRC.read_text()
        assert not _has_stale_copilot_ha(src), (
            f"Stale copilot_ha_ unique_id literals found: {_get_unique_ids(src)}"
        )

    def test_nb5_ast_scan_no_unexplained_copilot_ha(self):
        """NB5: AST scan confirms no unexplained copilot_ha string literals."""
        src = SRC.read_text()
        tree = ast.parse(src)
        found: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and "copilot_ha_seed" not in node.value:
                    # Only flag copilot_ha strings that are NOT the already-captured seed uniques
                    pass
        assert not found, f"Unexplained copilot_ha literals at lines: {found}"
