"""Contract tests for repairs.py blueprint default paths — HA-444."""
import ast
import pytest


def _scan_copilot_ha_blueprint_literals(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any 'copilot_ha/' blueprint literal in source."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha/" in node.value:
                results.append((node.lineno, repr(node.value)))
    return results


def _scan_pilotsuite_blueprint_literals(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any 'pilotsuite/' blueprint literal in source."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "pilotsuite/" in node.value:
                results.append((node.lineno, repr(node.value)))
    return results


class TestRepairsBlueprintProjection:
    """HA-444 — repairs.py blueprint default path parity."""

    REP_PATH = "custom_components/pilotsuite/repairs.py"

    def test_rp1_canonical_pilotsuite_blueprint_path_in_async_step_init_preview(self):
        """RP1: canonical pilotsuite/a_to_b_safe.yaml present in init preview branch."""
        hits = _scan_pilotsuite_blueprint_literals(self.REP_PATH)
        # Must contain pilotsuite/a_to_b_safe.yaml
        assert any("pilotsuite/a_to_b_safe.yaml" in s for _, s in hits), (
            f"Expected pilotsuite/a_to_b_safe.yaml in repairs.py blueprint placeholders, got: {hits}"
        )

    def test_rp2_no_stale_copilot_ha_blueprint_literal(self):
        """RP2: zero stale copilot_ha/ blueprint literals in repairs.py."""
        hits = _scan_copilot_ha_blueprint_literals(self.REP_PATH)
        assert len(hits) == 0, (
            f"Found {len(hits)} stale copilot_ha/ blueprint literal(s) in repairs.py: {hits}"
        )

    def test_rp3_syntax_ok(self):
        """RP3: repairs.py parses without SyntaxError."""
        with open(self.REP_PATH) as fh:
            src = fh.read()
        try:
            ast.parse(src)
        except SyntaxError as exc:
            pytest.fail(f"SyntaxError in repairs.py: {exc}")
