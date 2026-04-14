"""Contract tests for suggest.py blueprint_id — HA-445."""
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


class TestSuggestBlueprintProjection:
    """HA-445 — suggest.py blueprint_id parity."""

    SUG_PATH = "custom_components/pilotsuite/suggest.py"

    def test_sg1_canonical_pilotsuite_blueprint_id_in_async_offer_candidate(self):
        """SG1: canonical pilotsuite/a_to_b_safe.yaml present in async_offer_candidate."""
        hits = _scan_pilotsuite_blueprint_literals(self.SUG_PATH)
        # Must contain pilotsuite/a_to_b_safe.yaml
        assert any("pilotsuite/a_to_b_safe.yaml" in s for _, s in hits), (
            f"Expected pilotsuite/a_to_b_safe.yaml in suggest.py blueprint placeholders, got: {hits}"
        )

    def test_sg2_no_stale_copilot_ha_blueprint_literal(self):
        """SG2: zero stale copilot_ha/ blueprint literals in suggest.py."""
        hits = _scan_copilot_ha_blueprint_literals(self.SUG_PATH)
        assert len(hits) == 0, (
            f"Found {len(hits)} stale copilot_ha/ blueprint literal(s) in suggest.py: {hits}"
        )

    def test_sg3_syntax_ok(self):
        """SG3: suggest.py parses without SyntaxError."""
        with open(self.SUG_PATH) as fh:
            src = fh.read()
        try:
            ast.parse(src)
        except SyntaxError as exc:
            pytest.fail(f"SyntaxError in suggest.py: {exc}")