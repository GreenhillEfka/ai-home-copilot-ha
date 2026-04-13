"""Projection contract tests for ha_errors_digest.py (HA-421)."""
import ast


def _parse(path):
    with open(path) as f:
        return ast.parse(f.read())


def _find_pilotsuite_ha_errors_digest_strings(tree):
    """Find string literals equal to pilotsuite_ha_errors_digest."""
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value == "pilotsuite_ha_errors_digest":
                hits.append(node.value)
    return hits


def _has_stale_copilot_ha_strings(tree):
    """Return True if any string literal contains stale copilot_ha notification id."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha_ha_errors_digest" in node.value:
                return True
    return False


class TestHaErrorsDigestProjection:
    """HA-421: ha_errors_digest.py notification_id parity."""

    def test_ed1_canonical_notification_id_async_show(self):
        """ED1: async_show_ha_errors_digest uses pilotsuite_ha_errors_digest."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        hits = _find_pilotsuite_ha_errors_digest_strings(tree)
        assert "pilotsuite_ha_errors_digest" in hits, (
            f"Expected pilotsuite_ha_errors_digest in string literals, got: {hits}"
        )

    def test_ed2_canonical_notification_id_async_setup_tick(self):
        """ED2: _tick inner uses pilotsuite_ha_errors_digest."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        hits = _find_pilotsuite_ha_errors_digest_strings(tree)
        assert hits.count("pilotsuite_ha_errors_digest") == 2, (
            f"Expected exactly 2 pilotsuite_ha_errors_digest hits, got {hits}"
        )

    def test_ed3_ast_scan_null_stale_copilot_ha_notification_id(self):
        """ED3: AST scan confirms zero stale copilot_ha_ha_errors_digest literals."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        stale = _has_stale_copilot_ha_strings(tree)
        assert not stale, "Found stale copilot_ha_ha_errors_digest in ha_errors_digest.py"