"""Projection contract for config_options_flow.py legacy www path parity.

HA-480: Ensure config_options_flow.py user-facing description strings
use the canonical pilotsuite www path, not the stale copilot_ha/ path.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "config_options_flow.py"


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestConfigOptionsFlowProjection:
    """Legacy path reference contract for config_options_flow.py."""

    def test_cof1_no_stale_copilot_ha_www_path_in_generate_step(self) -> None:
        """COF1: async_step_generate_dashboard description contains no stale copilot_ha/ path."""
        source = _read_source()
        # The generate step description should reference pilotsuite/, not copilot_ha/
        assert "copilot_ha/" not in re.search(
            r'async_step_generate_dashboard.*?"[^"]+"',
            source, re.DOTALL
        ).group(), (
            "async_step_generate_dashboard description must not reference "
            "the stale copilot_ha/ legacy path"
        )

    def test_cof2_no_stale_copilot_ha_www_path_in_publish_step(self) -> None:
        """COF2: async_step_publish_dashboard description contains no stale copilot_ha/ path."""
        source = _read_source()
        # The publish step description should reference www/pilotsuite/, not www/copilot_ha/
        assert "www/copilot_ha/" not in source, (
            "async_step_publish_dashboard description must not reference "
            "the stale www/copilot_ha/ legacy path; use www/pilotsuite/ instead"
        )

    def test_cof3_canonical_pilotsuite_www_path_present(self) -> None:
        """COF3: Both description strings reference the canonical pilotsuite path."""
        source = _read_source()
        # Both description blocks should reference the canonical pilotsuite path
        assert "(with legacy mirror in `pilotsuite/`)" in source, (
            "async_step_generate_dashboard description should reference "
            "the canonical pilotsuite/ legacy mirror path"
        )
        assert "(plus legacy mirror in `www/pilotsuite/`)" in source, (
            "async_step_publish_dashboard description should reference "
            "the canonical www/pilotsuite/ legacy mirror path"
        )

    def test_cof4_ast_scan_no_remaining_copilot_ha_www_string(self) -> None:
        """COF4: AST scan finds no copilot_ha/ string literals in config_options_flow.py."""
        source = _read_source()
        # Filter out legitimate legacy migration comments
        lines = [
            line for line in source.splitlines()
            if "copilot_ha" in line.lower()
            and "legacy" not in line.lower()
            and "migration" not in line.lower()
            and "backward" not in line.lower()
        ]
        assert len(lines) == 0, (
            f"Found {len(lines)} remaining copilot_ha references outside "
            f"legacy migration comments: {lines}"
        )

    def test_cof5_syntax_ok(self) -> None:
        """COF5: config_options_flow.py parses without syntax errors."""
        source = _read_source()
        try:
            ast.parse(source, filename=str(TARGET_FILE))
        except SyntaxError as exc:
            pytest.fail(f"Syntax error in config_options_flow.py: {exc}")
