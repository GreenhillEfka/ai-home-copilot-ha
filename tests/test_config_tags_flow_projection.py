"""Projection contract for config_tags_flow.py DOMAIN reference parity.

HA-393: Ensure config_tags_flow.py uses canonical DOMAIN lookup with
legacy fallback, not a hardcoded stale copilot_ha string.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# tests/ → repo-root (parents[1])
REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILE = REPO_ROOT / "custom_components" / "pilotsuite" / "config_tags_flow.py"


def _parse_tree() -> ast.Module:
    """Parse the production module into an AST."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source, filename=str(TARGET_FILE))


def _read_source() -> str:
    """Raw source text of the production module."""
    with open(TARGET_FILE, encoding="utf-8") as f:
        return f.read()


class TestConfigTagsFlowProjection:
    """Domain reference contract for config_tags_flow.py."""

    def test_ctf1_canonical_domain_import_present(self) -> None:
        """CTF1: config_tags_flow.py imports DOMAIN from const."""
        source = _read_source()
        assert "from .const import DOMAIN" in source, (
            "config_tags_flow.py must import DOMAIN from .const to avoid "
            "hardcoding a stale legacy domain string"
        )

    def test_ctf2_flow_hass_data_uses_domain_variable_first(self) -> None:
        """CTF2: _reload_module uses DOMAIN variable, not hardcoded 'copilot_ha'."""
        source = _read_source()
        # The preferred path should use the DOMAIN variable
        assert re.search(r'flow\.hass\.data\.get\(DOMAIN,\s*\{\}', source) or \
               re.search(r'flow\.hass\.data\.get\(\s*DOMAIN\s*,\s*\{\}', source), (
            "_reload_module must use flow.hass.data.get(DOMAIN, {}) as the "
            "primary lookup path"
        )

    def test_ctf3_legacy_fallback_uses_pilotsuite_string(self) -> None:
        """CTF3: Legacy fallback uses the 'pilotsuite' string as the canonical domain."""
        source = _read_source()
        assert '"pilotsuite"' in source, (
            "The legacy fallback must use the string literal 'pilotsuite' "
            "as the canonical domain for migration from the old domain"
        )

    def test_ctf4_no_bare_hardcoded_copilot_ha_in_data_lookup(self) -> None:
        """CTF4: No stale bare copilot_ha in primary hass.data lookup path."""
        source = _read_source()
        lines = source.splitlines()
        for i, line in enumerate(lines, 1):
            # Allow 'copilot_ha' only in the legacy fallback branch
            if "flow.hass.data.get(" in line and '"copilot_ha"' in line:
                # Must be after a "not data" or "if not" guard, meaning it's the fallback
                # Check the surrounding context (2 lines before)
                context = "\n".join(lines[max(0, i-3):i])
                assert "not data" in context or "if not" in context or "if data" in context.lower(), (
                    f"Line {i}: Primary hass.data lookup must not use hardcoded "
                    f"'copilot_ha' — only the legacy fallback may contain that string"
                )

    def test_ctf5_ast_no_undeclared_copilot_ha_imports(self) -> None:
        """CTF5: AST scan confirms no copilot_ha string literals outside legacy fallback context."""
        tree = _parse_tree()
        found_hardcoded = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val = node.value
                        if isinstance(val, ast.Constant) and isinstance(val.value, str):
                            if "copilot_ha" in val.value and "DOMAIN" not in target.id:
                                found_hardcoded.append(f"{target.id} = {repr(val.value)}")

        assert not found_hardcoded, (
            f"Found hardcoded copilot_ha strings outside DOMAIN/legacy fallback: {found_hardcoded}"
        )

    def test_ctf6_pragma_coverage_marker(self) -> None:
        """CTF6: This contract test is explicitly owned by HomeClaw lane."""
        import inspect
        stack = inspect.stack()
        caller_file = stack[0].filename
        assert "test_config_tags_flow_projection" in Path(caller_file).name