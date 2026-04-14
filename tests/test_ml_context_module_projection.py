"""Contract tests for ml_context_module projection parity."""
import ast
import re


def test_ml_context_module_pilotsuite_hass_data_keys():
    """ML1: ml_context_module uses pilotsuite hass.data keys."""
    with open("custom_components/pilotsuite/core/modules/ml_context_module.py") as f:
        content = f.read()
    # Verify pilotsuite key is used
    assert 'hass.data.get("pilotsuite"' in content or "hass.data['pilotsuite']" in content
    # Verify storage path uses pilotsuite
    assert "/config/.storage/pilotsuite/ml" in content


def test_ml_context_module_ast_scan_no_stale_copilot_ha():
    """ML2: AST scan confirms no stale copilot_ha literals in ml_context_module."""
    with open("custom_components/pilotsuite/core/modules/ml_context_module.py") as f:
        content = f.read()
    tree = ast.parse(content)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value:
                found.append(node.value)
    # Filter out comments/docstrings
    stale = [v for v in found if "copilot_ha" in v and "pilotsuite" not in v]
    assert len(stale) == 0, f"Stale copilot_ha literals found: {stale}"


def test_ml_context_module_syntax_ok():
    """ML3: Syntax is valid."""
    with open("custom_components/pilotsuite/core/modules/ml_context_module.py") as f:
        content = f.read()
    ast.parse(content)
