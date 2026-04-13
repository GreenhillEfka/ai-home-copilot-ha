"""Projection contract tests for core_proxy.py (HA-427)."""
import ast


def _parse(path):
    with open(path) as f:
        return ast.parse(f.read())


def _has_stale_copilot_ha_name(tree):
    """Return True if the CoreProxyView name field contains stale copilot_ha."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "name":
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        if "copilot_ha" in node.value.value:
                            return True
    return False


class TestCoreProxyProjection:
    """HA-427: core_proxy.py api name field parity."""

    def test_canonical_pilotsuite_name(self):
        """CP1: CoreProxyView.name uses canonical pilotsuite reference."""
        path = "custom_components/pilotsuite/core_proxy.py"
        tree = _parse(path)
        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "name":
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            assert node.value.value == "api:pilotsuite:core_proxy", (
                                f"Expected name='api:pilotsuite:core_proxy', "
                                f"got name={node.value.value!r}"
                            )
                            found = True
        assert found, "CoreProxyView.name assignment not found"

    def test_null_stale_copilot_ha_name(self):
        """CP2: CoreProxyView.name contains no stale copilot_ha literal."""
        path = "custom_components/pilotsuite/core_proxy.py"
        tree = _parse(path)
        assert not _has_stale_copilot_ha_name(tree), (
            "Found stale 'copilot_ha' in CoreProxyView.name field"
        )

    def test_ast_scan_no_copilot_ha_hardcodes(self):
        """CP3: AST scan — no unexplained copilot_ha string literals in core_proxy.py."""
        path = "custom_components/pilotsuite/core_proxy.py"
        tree = _parse(path)
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    hits.append(node.value)
        # Filter known intentional uses (URL path /api/copilot_proxy/ is routing, not name)
        stale = [h for h in hits if h != "/api/copilot_proxy/{tail:.*}"]
        assert not stale, f"Unexpected copilot_ha literals: {stale}"
