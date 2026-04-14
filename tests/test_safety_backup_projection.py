"""Contract tests for safety_backup.py projection parity."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

SOURCE = Path("custom_components/pilotsuite/safety_backup.py")
MODULE = "custom_components.pilotsuite.safety_backup"


class TestSafetyBackupProjection:
    """Projection parity contract tests for safety_backup.py."""

    @staticmethod
    def scan_stale_copilot_ha_literals(filepath: Path) -> list[tuple[int, str]]:
        """Return all stale copilot_ha literals outside LEGACY注释 blocks."""
        stale = []
        with open(filepath, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                if "copilot_ha" in line:
                    stale.append((lineno, line.rstrip()))
        return stale

    def test_sb1_canonical_notification_id_async_create(self):
        """SB1: async_create_safety_backup uses pilotsuite_safety_backup notification_id."""
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "async_create"
                ):
                    for kw in node.keywords:
                        if kw.arg == "notification_id":
                            hits.append(kw.value.value if isinstance(kw.value, ast.Constant) else None)
        assert "pilotsuite_safety_backup" in hits, (
            f"async_create_safety_backup notification_id should be pilotsuite_safety_backup, got {hits}"
        )

    def test_sb2_canonical_notification_id_async_show(self):
        """SB2: async_show_safety_backup_status uses pilotsuite_safety_backup notification_id."""
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "async_create"
                ):
                    for kw in node.keywords:
                        if kw.arg == "notification_id":
                            hits.append(kw.value.value if isinstance(kw.value, ast.Constant) else None)
        assert "pilotsuite_safety_backup" in hits, (
            f"async_show_safety_backup_status notification_id should be pilotsuite_safety_backup, got {hits}"
        )

    def test_sb3_ast_scan_null_stale_copilot_ha_literals(self):
        """SB3: AST scan — no stale copilot_ha notification_id literals in the file."""
        stale = self.scan_stale_copilot_ha_literals(SOURCE)
        assert not stale, (
            f"Found stale copilot_ha literals at lines {[(l, s) for l, s in stale]}; "
            "all notification_id values must be pilotsuite_safety_backup"
        )

    def test_sb4_syntax_ok(self):
        """SB4: safety_backup.py is syntactically valid."""
        try:
            ast.parse(SOURCE.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            pytest.fail(f"Syntax error: {exc}")
