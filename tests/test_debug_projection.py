"""Contract tests: debug.py projection parity (HA-446)."""

import ast
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent / "custom_components" / "pilotsuite"
DEBUG_PY = ROOT / "debug.py"


class TestDebugProjectionParity:
    """Verify debug.py uses pilotsuite storage key, not copilot_ha."""

    def test_db1_canonical_storage_key(self):
        """DB1: Store is initialized with canonical pilotsuite_debug_state key."""
        src = DEBUG_PY.read_text()
        tree = ast.parse(src)

        # Find DEBUG_STORAGE_KEY assignment
        storage_key = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "DEBUG_STORAGE_KEY":
                        if isinstance(node.value, ast.Constant):
                            storage_key = node.value.value

        assert storage_key == "pilotsuite_debug_state", (
            f"Expected DEBUG_STORAGE_KEY='pilotsuite_debug_state', got {storage_key!r}"
        )

    def test_db2_no_stale_copilot_ha_literal(self):
        """DB2: AST scan finds zero stale copilot_ha literals in debug.py."""
        src = DEBUG_PY.read_text()
        tree = ast.parse(src)

        stale = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    stale.append(node.value)

        assert not stale, f"Found stale copilot_ha literals: {stale}"

    def test_db3_syntax_ok(self):
        """DB3: debug.py parses without syntax errors."""
        src = DEBUG_PY.read_text()
        tree = ast.parse(src)
        assert tree is not None
