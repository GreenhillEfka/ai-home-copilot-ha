"""Contract tests for entity_tags_module copilot_ha → pilotsuite parity."""
import ast
import pytest

SRC = "custom_components/pilotsuite/core/modules/entity_tags_module.py"


class TestEntityTagsModuleProjection:
    """Verify entity_tags_module uses only pilotsuite hass.data keys."""

    def test_et1_canonical_pilotsuite_hass_data_keys(self):
        """ET1: entity_tags_module uses pilotsuite.* hass.data keys."""
        with open(SRC) as f:
            src = f.read()
        # The module must use pilotsuite domain for hass.data
        assert 'hass.data.get("pilotsuite"' in src or "hass.data.get('pilotsuite'" in src
        assert 'hass.data.setdefault("pilotsuite"' in src or "hass.data.setdefault('pilotsuite'" in src

    def test_et2_ast_scan_no_stale_copilot_ha_hass_data(self):
        """ET2: AST scan finds zero stale copilot_ha hass.data literals."""
        with open(SRC) as f:
            src = f.read()
        tree = ast.parse(src)

        # Find all string literals that look like stale hass.data copilot_ha keys
        stale_literals = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                # Only flag actual runtime keys (not paths, not tests)
                if "copilot_ha" in val and (
                    '.get("copilot_ha' in src[max(0, node.col_offset - 5):node.col_offset + 30]  # noqa
                    or '.setdefault("copilot_ha' in src[max(0, node.col_offset - 5):node.col_offset + 35]  # noqa
                    or '["copilot_ha"]' in src[max(0, node.col_offset - 5):node.col_offset + 30]  # noqa
                ):
                    stale_literals.append(val)

        assert not stale_literals, f"Stale copilot_ha hass.data keys found: {stale_literals}"

    def test_et3_syntax_ok(self):
        """ET3: entity_tags_module.py parses without syntax errors."""
        with open(SRC) as f:
            src = f.read()
        try:
            ast.parse(src)
        except SyntaxError as exc:
            pytest.fail(f"Syntax error: {exc}")
