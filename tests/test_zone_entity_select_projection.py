"""Contract tests for zone_entity_select.py — HA-456."""
import ast
import pytest


def _scan_copilot_ha_literals(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any 'copilot_ha' literal in source."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                results.append((node.lineno, repr(node.value)))
    return results


def _scan_pilotsuite_literals(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any 'pilotsuite' literal in source."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "pilotsuite" in node.value:
                results.append((node.lineno, repr(node.value)))
    return results


class TestZoneEntitySelectProjection:
    """HA-456 — zone_entity_select.py docstring copilot_ha → pilotsuite parity."""

    ZES_PATH = "custom_components/pilotsuite/zone_entity_select.py"

    def test_zd1_canonical_pilotsuite_ref_in_find_entry_id_docstring(self):
        """ZD1: canonical 'pilotsuite config entry ID' present in _find_entry_id docstring."""
        hits = _scan_pilotsuite_literals(self.ZES_PATH)
        # Must contain "pilotsuite config entry ID" (not copilot_ha)
        assert any("pilotsuite" in s and "config entry ID" in s for _, s in hits), (
            f"Expected 'pilotsuite config entry ID' in zone_entity_select.py docstring, got: {hits}"
        )

    def test_zd2_no_stale_copilot_ha_literal(self):
        """ZD2: zero stale 'copilot_ha' literals in zone_entity_select.py."""
        hits = _scan_copilot_ha_literals(self.ZES_PATH)
        assert len(hits) == 0, (
            f"Found {len(hits)} stale copilot_ha literal(s) in zone_entity_select.py: {hits}"
        )

    def test_zd3_syntax_ok(self):
        """ZD3: zone_entity_select.py parses without SyntaxError."""
        with open(self.ZES_PATH) as fh:
            src = fh.read()
        try:
            ast.parse(src)
        except SyntaxError as exc:
            pytest.fail(f"SyntaxError in zone_entity_select.py: {exc}")
