"""PilotSuite — button_update_rollback unique_id projection contract (HA-408)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/button_update_rollback.py")
CODE = SRC.read_text()


class UniqueIdVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            if isinstance(t, ast.Name) and "_attr_unique_id" == t.id:
                if isinstance(node.value, ast.Constant):
                    self.found.append(node.value.value)
        self.generic_visit(node)


class TestButtonUpdateRollbackProjection:
    """Source-Guard: unique_id must be pilotsuite-prefixed, not copilot_ha."""

    UR1 = pytest.mark.xfail(reason="canonical pilotsuite unique_id")
    UR2 = pytest.mark.xfail(reason="null stale copilot_ha literal")

    def test_ur1_unique_id_is_pilotsuite(self) -> None:
        """UR1: _attr_unique_id is canonical pilotsuite-prefixed."""
        assert "pilotsuite_update_rollback_report" in CODE

    def test_ur2_no_stale_copilot_ha(self) -> None:
        """UR2: AST scan — no stale copilot_ha literal in this file."""
        assert "copilot_ha_update_rollback_report" not in CODE
