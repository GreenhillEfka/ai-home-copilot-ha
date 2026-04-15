"""Contract tests for candidate_poller.py service docstring — HA-476."""
import ast


def _scan_copilot_ha_trigger_mining_docstrings(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any stale copilot_ha.trigger_mining docstring literal."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc and "copilot_ha.trigger_mining" in doc:
                results.append((node.lineno, repr(doc)))
    return results


def _scan_pilotsuite_trigger_mining_docstrings(filepath: str) -> list[tuple[int, str]]:
    """Return (lineno, line) for any canonical pilotsuite.trigger_mining docstring."""
    with open(filepath) as fh:
        source = fh.read()
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc and "pilotsuite.trigger_mining" in doc:
                results.append((node.lineno, repr(doc)))
    return results


def test_canonical_pilotsuite_trigger_mining_docstring():
    """CP-S1: canonical pilotsuite.trigger_mining in _register_mining_service docstring."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    hits = _scan_pilotsuite_trigger_mining_docstrings(filepath)
    assert any("pilotsuite.trigger_mining" in doc for _, doc in hits), (
        f"Expected pilotsuite.trigger_mining in _register_mining_service docstring; "
        f"found: {hits}"
    )


def test_no_stale_copilot_ha_trigger_mining_docstring():
    """CP-S2: zero stale copilot_ha.trigger_mining docstrings in candidate_poller.py."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    hits = _scan_copilot_ha_trigger_mining_docstrings(filepath)
    assert not hits, f"Stale copilot_ha.trigger_mining docstrings found: {hits}"


def test_syntax_ok():
    """CP-S3: candidate_poller.py parses without syntax errors."""
    filepath = "custom_components/pilotsuite/core/modules/candidate_poller.py"
    with open(filepath) as fh:
        source = fh.read()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in {filepath}: {exc}")