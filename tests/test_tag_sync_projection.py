"""Contract tests: tag_sync.py projection parity (HA-473)."""

import ast
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent / "custom_components" / "pilotsuite"
TAG_SYNC_PY = ROOT / "tag_sync.py"


class TestTagSyncProjectionParity:
    """Verify tag_sync.py uses pilotsuite in error strings, not copilot_ha."""

    def test_ts1_canonical_domain_in_error_strings(self):
        """TS1: _resolve_entry uses pilotsuite domain in error/LOG strings."""
        src = TAG_SYNC_PY.read_text()
        tree = ast.parse(src)

        stale = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    stale.append((node.lineno, node.value))

        assert not stale, f"Found stale copilot_ha string literals at lines: {stale}"

    def test_ts2_ast_scan_no_stale_copilot_ha(self):
        """TS2: AST scan finds zero unexplained copilot_ha literals in tag_sync.py."""
        src = TAG_SYNC_PY.read_text()
        tree = ast.parse(src)

        stale = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and "pilotsuite" not in node.value:
                    stale.append((node.lineno, node.value))

        assert not stale, f"Unexplained copilot_ha literals found: {stale}"

    def test_ts3_syntax_ok(self):
        """TS3: tag_sync.py parses without syntax errors."""
        src = TAG_SYNC_PY.read_text()
        tree = ast.parse(src)
        assert tree is not None
