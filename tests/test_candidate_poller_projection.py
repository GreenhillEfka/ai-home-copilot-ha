"""Contract tests for candidate_poller.py blueprint default path — HA-454."""
import ast


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


def test_canonical_pilotsuite_blueprint_id_default():
    """CP1: canonical pilotsuite/a_to_b_safe.yaml as blueprint_id default."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    hits = _scan_pilotsuite_blueprint_literals(filepath)
    assert any("pilotsuite/a_to_b_safe.yaml" in val for _, val in hits), (
        f"Expected pilotsuite/a_to_b_safe.yaml as canonical blueprint_id default; "
        f"found: {hits}"
    )


def test_no_stale_copilot_ha_blueprint_literal():
    """CP2: zero stale copilot_ha/ blueprint literals in candidate_poller.py."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    hits = _scan_copilot_ha_blueprint_literals(filepath)
    assert not hits, f"Stale copilot_ha/ blueprint literals found: {hits}"


def test_syntax_ok():
    """CP3: candidate_poller.py parses without syntax errors."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    with open(filepath) as fh:
        source = fh.read()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in {filepath}: {exc}")
