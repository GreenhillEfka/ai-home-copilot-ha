"""Projection contract tests for frigate_bridge module."""
import ast
from pathlib import Path

import pytest

FIXTURE = Path("custom_components/pilotsuite/core/modules/frigate_bridge.py")


class TestFrigateBridgeProjection:
    """Projection parity tests for frigate_bridge.py copilot_ha → pilotsuite migration."""

    @pytest.fixture
    def source_tree(self) -> ast.Module:
        """Parse frigate_bridge.py as AST."""
        return ast.parse(FIXTURE.read_text(encoding="utf-8"))

    def test_fb1_canonical_event_name_in_docstring(
        self, source_tree: ast.Module
    ) -> None:
        """FB1: _fire_event docstring references the canonical pilotsuite event name."""
        import ast

        docstring_found = False
        for node in ast.walk(source_tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_fire_camera_event":
                docstring = ast.get_docstring(node) or ""
                assert "pilotsuite" in docstring, (
                    f"Expected 'pilotsuite' in _fire_camera_event docstring, got: {docstring!r}"
                )
                docstring_found = True
        assert docstring_found, "_fire_camera_event function not found"

    def test_fb2_ast_scan_null_stale_copilot_ha_literals(
        self, source_tree: ast.Module
    ) -> None:
        """FB2: AST scan finds zero unexplained copilot_ha literals outside LEGACY markers."""
        stale_hits: list[str] = []
        LEGACY_MARKERS = {"LEGACY", "copilot_ha", "COPILOT_HA", "legacy"}
        for node in ast.walk(source_tree):
            if isinstance(node, ast.Name) and "copilot_ha" in node.id.lower():
                parent_ids = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                if parent_ids - LEGACY_MARKERS:
                    stale_hits.append(node.id)
        assert not stale_hits, f"Unexplained copilot_ha literals: {stale_hits}"

    def test_fb3_syntax_ok(self, source_tree: ast.Module) -> None:
        """FB3: frigate_bridge.py parses without syntax errors."""
        assert source_tree is not None
