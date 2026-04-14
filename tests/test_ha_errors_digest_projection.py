"""Projection contract tests for ha_errors_digest.py (HA-441)."""
import ast


def _parse(path):
    with open(path) as f:
        return ast.parse(f.read())


def _find_match_substrings_pilotsuite(tree):
    """Find pilotsuite string literals in _MATCH_SUBSTRINGS."""
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.List) and hasattr(node, 'ctx') and isinstance(node.ctx, ast.Load):
            # Check if this list contains string constants with pilotsuite
            for elt in getattr(node, 'elts', []):
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    if 'pilotsuite' in elt.value:
                        hits.append(elt.value)
    return hits


def _find_stale_copilot_ha_pattern_strings(tree):
    """Return True if any string literal contains stale copilot_ha log pattern strings."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if 'copilot_ha' in node.value:
                return True
    return False


def _check_match_substrings_uses_pilotsuite(tree):
    """Verify _MATCH_SUBSTRINGS contains pilotsuite, custom_components.pilotsuite, custom integration pilotsuite."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '_MATCH_SUBSTRINGS':
                    if isinstance(node.value, ast.List):
                        vals = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
                        return (
                            'pilotsuite' in vals and
                            'custom_components.pilotsuite' in vals and
                            "custom integration 'pilotsuite'" in vals and
                            'copilot_ha' not in vals and
                            'custom_components.copilot_ha' not in vals and
                            "custom integration 'copilot_ha'" not in vals
                        )
    return False


def _check_is_relevant_entry_uses_pilotsuite(tree):
    """Verify _is_relevant_entry checks for pilotsuite strings, not copilot_ha."""
    source_lines = open('custom_components/pilotsuite/ha_errors_digest.py').read()
    # Check the function body contains pilotsuite checks
    func_start = source_lines.find('def _is_relevant_entry')
    func_end = source_lines.find('\ndef ', func_start + 1)
    func_body = source_lines[func_start:func_end] if func_end != -1 else source_lines[func_start:]
    # Must have pilotsuite checks
    has_pilotsuite = 'pilotsuite' in func_body
    # Must NOT have copilot_ha checks (except in legacy comments)
    copilot_ha_in_checks = '"copilot_ha"' in func_body or "'copilot_ha'" in func_body
    return has_pilotsuite and not copilot_ha_in_checks


class TestHaErrorsDigestProjection:
    """HA-441: ha_errors_digest.py _MATCH_SUBSTRINGS and _is_relevant_entry log pattern parity."""

    def test_ed1_match_substrings_uses_pilotsuite(self):
        """ED1: _MATCH_SUBSTRINGS contains pilotsuite signal strings, not copilot_ha."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        ok = _check_match_substrings_uses_pilotsuite(tree)
        assert ok, (
            "_MATCH_SUBSTRINGS must contain 'pilotsuite', "
            "'custom_components.pilotsuite', \"custom integration 'pilotsuite'\" "
            "and must NOT contain copilot_ha variants"
        )

    def test_ed2_is_relevant_entry_checks_pilotsuite(self):
        """ED2: _is_relevant_entry checks for pilotsuite strings, not copilot_ha."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        ok = _check_is_relevant_entry_uses_pilotsuite(tree)
        assert ok, (
            "_is_relevant_entry must check for 'pilotsuite' and "
            "'custom_components.pilotsuite' strings, not copilot_ha variants"
        )

    def test_ed3_ast_scan_null_stale_copilot_ha_pattern_strings(self):
        """ED3: AST scan confirms zero stale copilot_ha log-pattern strings in the file."""
        path = "custom_components/pilotsuite/ha_errors_digest.py"
        tree = _parse(path)
        stale = _find_stale_copilot_ha_pattern_strings(tree)
        assert not stale, (
            "Found stale copilot_ha log-pattern string literal in ha_errors_digest.py"
        )