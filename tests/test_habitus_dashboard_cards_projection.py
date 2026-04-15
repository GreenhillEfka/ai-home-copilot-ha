"""Projection Contract Tests — habitus_dashboard_cards markdown URL (HA-477).

Verifies habitus_dashboard_cards.py markdown card for the configuration link
references the canonical /config/pilotsuite/zones path instead of the legacy
/config/copilot_ha/zones path.

HA-477 — 2026-04-15
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

FIXTURE = Path("custom_components/pilotsuite/habitus_dashboard_cards.py")
FIXTURE_SOURCE = FIXTURE.read_text(encoding="utf-8")


class TestHabitusDashboardCardsProjection:
    """Projection parity tests for habitus_dashboard_cards.py copilot_ha → pilotsuite migration."""

    @pytest.fixture
    def source_tree(self) -> ast.Module:
        """Parse habitus_dashboard_cards.py as AST."""
        return ast.parse(FIXTURE_SOURCE, filename=str(FIXTURE))

    def test_hdc1_canonical_zones_url_in_source(self, source_tree: ast.Module) -> None:
        """HDC1: source must contain /config/pilotsuite/zones (canonical URL at L344)."""
        assert "/config/pilotsuite/zones" in FIXTURE_SOURCE, (
            f"Expected /config/pilotsuite/zones in source at L344, not found"
        )

    def test_hdc2_no_legacy_copilot_ha_zones_url(self, source_tree: ast.Module) -> None:
        """HDC2: source must not contain legacy /config/copilot_ha/zones URL."""
        assert "/config/copilot_ha/zones" not in FIXTURE_SOURCE, (
            f"Legacy URL /config/copilot_ha/zones found in source at L344"
        )

    def test_hdc3_ast_no_copilot_ha_string_literals(self, source_tree: ast.Module) -> None:
        """HDC3: habitus_dashboard_cards.py must not contain copilot_ha string literals
        (excluding LEGACY markers in const.py and comments)."""
        for node in ast.walk(source_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                # Only fail if copilot_ha appears WITHOUT pilotsuite also present
                if "copilot_ha" in val and "pilotsuite" not in val:
                    pytest.fail(f"Unexpected copilot_ha literal found: {ast.dump(node)}")

    def test_hdc4_syntax_ok(self, source_tree: ast.Module) -> None:
        """HDC4: habitus_dashboard_cards.py must compile without syntax errors."""
        assert source_tree is not None